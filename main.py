import os
import asyncio
import re
from datetime import datetime, UTC, timedelta
from typing import Optional
from fastapi import FastAPI, Depends, Request, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from sqlmodel import Session, select, or_
from services.streaming_manager import streaming_manager
from models import init_db, get_engine, Conversation, Device, SensorReading
from config import get_settings

app = FastAPI(title="Backend Plant Pot", version="2.0.0")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()
    settings = get_settings()
    if not os.path.exists(settings.STORAGE_PATH):
        os.makedirs(settings.STORAGE_PATH)
    
    # Pre-generate hmm.mp3 for warm start (optional but recommended)
    warmup_path = os.path.join(settings.STORAGE_PATH, "hmm.mp3")
    if not os.path.exists(warmup_path):
        import shutil
        # Place a dummy silent mp3 if needed, or just touch the file
        open(warmup_path, 'a').close()

# Mount static files for simulator and audio data
app.mount("/simulator", StaticFiles(directory="simulator"), name="simulator")
app.mount("/audio", StaticFiles(directory="audio_artifacts"), name="audio")

def get_session():
    with Session(get_engine()) as session:
        yield session

from agents.orchestrator import create_pot_graph
from services.transcription import TranscriptionService
from services.speech_synthesis import SpeechSynthesisService

async def streaming_agent_task(convo_id: str, device_id: str, species: str, user_query: str, sensor_text: str, know_text: str, sensor_data: dict):
    """Background task to run the agent in streaming mode."""
    from agents.conversation_agent import ConversationAgent
    agent = ConversationAgent()
    
    state = {
        "device_id": device_id,
        "species": species,
        "user_query": user_query,
        "sensor_analysis": sensor_text,
        "plant_knowledge": know_text,
        "sensor_data": sensor_data
    }
    
    full_response = ""
    mood = "neutral"
    
    try:
        async for chunk in agent.stream_run(state):
            if chunk["type"] == "metadata":
                mood = chunk["mood"]
                # For now just log metadata, but could be pushed to a separate status endpoint
                await streaming_manager.put(convo_id, chunk)
            elif chunk["type"] == "sentence":
                text = chunk["text"]
                full_response += " " + text
                await streaming_manager.put(convo_id, chunk)
    except Exception as e:
        print(f"ERROR: [Agent Task] {e}")
    finally:
        print(f"✅ [AGENT] Final Response: {full_response.strip()}")
        streaming_manager.finish_stream(convo_id)
        # Final archival once finished
        asyncio.create_task(archive_conversation_task(device_id, user_query, full_response.strip(), convo_id))

async def archive_conversation_task(device_id: str, transcription: str, ai_response: str, convo_id: str):
    """Background task to archive conversation once streaming is complete."""
    from models import get_engine, Conversation
    from sqlmodel import Session
    from datetime import datetime
    
    try:
        with Session(get_engine()) as session:
            convo = Conversation(
                id=int(convo_id),
                device_id=device_id,
                transcription=transcription,
                ai_response=ai_response,
                audio_file_path=f"streamed_{convo_id}.mp3" # Placeholder
            )
            session.add(convo)
            session.commit()
    except Exception as e:
        print(f"DEBUG: Archiver failed: {e}")

@app.post("/v1/ingest")
async def ingest_v1(
    background_tasks: BackgroundTasks,
    request: Request,
    device_id: str,
    temperature: float = 25.0,
    moisture: float = 50.0,
    light: float = 80.0,
    event: Optional[str] = None,
    user_query: Optional[str] = None,
    audio: Optional[UploadFile] = File(None),
    session: Session = Depends(get_session)
):
    # Retrieve or Create Device
    device = session.exec(select(Device).where(Device.id == device_id)).first()
    if not device:
        print(f"🆕 [DATABASE] Creating new device record for {device_id}")
        device = Device(id=device_id, name=f"Plant_{device_id[:4]}", species="Peace Lily")
        session.add(device)
        session.commit()
        session.refresh(device)

    # ... (Rest of Sensor Override and STT logic remains same as heritage)
    used_hardware_data = False
    if getattr(device, "is_simulator", False):
        ten_mins_ago = datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=10)
        statement = select(SensorReading).join(Device).where(Device.is_simulator == False, SensorReading.timestamp >= ten_mins_ago).order_by(SensorReading.timestamp.desc()).limit(1)
        recent_reading = session.exec(statement).first()
        if recent_reading:
            temperature = getattr(recent_reading, "temperature", temperature)
            light = getattr(recent_reading, "light", light)
            hw_moisture = getattr(recent_reading, "moisture", 0.0)
            if hw_moisture > 0.0: moisture = hw_moisture
            used_hardware_data = True

    force_notification = (event == "low_moisture_alert")
    
    # --- [LOGGING] DETAILED INGEST (What was received) ---
    print(f"\n📥 [INGEST] Received from {device_id}:")
    print(f"   🌡️ Temp:      {temperature:.1f}°C")
    print(f"   💧 Moisture:  {moisture:.1f}%")
    print(f"   ☀️ Light:     {light:.1f}%")
    print(f"   ✨ Event:     {event or 'None'}")
    print(f"   💬 Query:     {user_query or 'None'}")
    if audio:
        print(f"   🎙️ Audio:     {audio.filename} ({audio.content_type})")
    print(f"-----------------------------------\n")

    reading = SensorReading(device_id=device_id, temperature=temperature, moisture=moisture, light=light, event=event)
    session.add(reading)
    session.commit()

    if not user_query and audio:
        from services.storage import StorageService
        storage = StorageService()
        audio_path = await storage.save_audio(audio, device_id)
        stt = TranscriptionService()
        try:
            user_query = await stt.transcribe(audio_path)
        except Exception:
            user_query = ""
    
    settings = get_settings()
    if event == "wake_word" and not user_query:
        user_query = settings.WAKE_WORD

    # --- [SPEED OPTIMIZATION] PRE-GENERATE CONVO ID ---
    # We need a convo_id immediately to return to the ESP32
    convo_id = str(int(datetime.now().timestamp()))
    streaming_manager.start_stream(convo_id)
    
    # Fire off the agent thinking as a background task
    keywords_sensors = ["light", "moisture", "water", "temperature", "temp", "hungry", "health", "care", "how are you", "routine", "advice"]
    is_sensor_query = any(k in (user_query or "").lower() for k in keywords_sensors)
    from agents.orchestrator import fast_find_knowledge
    local_knowledge = fast_find_knowledge(device.species) if (user_query and len(user_query) > 3) else None
    
    sensor_text = f"Temp: {temperature}, Moisture: {moisture}, Light: {light}" if is_sensor_query else "Not requested."
    know_text = f"{local_knowledge.biological_info} {local_knowledge.care_tips}" if local_knowledge else "No local data found."

    if user_query or audio:
        background_tasks.add_task(
            streaming_agent_task, 
            convo_id, device_id, device.species, user_query or "...", 
            sensor_text, know_text, 
            {"temperature": temperature, "moisture": moisture, "light": light}
        )

    # 4. Immediate Dispatch - RELATIVE URL
    audio_url = f"/v1/audio/stream/{convo_id}"
    print(f"🚀 [DISPATCH] Sending Response Link: {audio_url}")
    return {
        "id": convo_id,
        "reply_text": "...", # Thinking...
        "audio_url": audio_url,
        "user_query": user_query or "...",
        "display": {"mood": "neutral"}
    }

def strip_mp3_header(audio_data: bytes) -> bytes:
    """Strips the ID3/Xing header to allow seamless joining of MP3 files."""
    # Robust sync finder: Look for 0xFF then another byte with high nibble 0xF (MP3 Sync)
    for i in range(len(audio_data) - 1):
        if audio_data[i] == 0xFF and (audio_data[i+1] & 0xF0) == 0xF0:
            print(f"✂️ [MP3] Found sync frame at byte {i}. Stripping header...")
            return audio_data[i:]
    print("⚠️ [MP3] No sync frame found in audio chunk!")
    return audio_data

@app.get("/v1/audio/stream/{convo_id}")
async def stream_audio(convo_id: str):
    """
    Real-time pipelined streaming endpoint. 
    Synthesizes sentences as they are emitted by the agent.
    """
    async def audio_stream_generator():
        import asyncio
        tts = SpeechSynthesisService()
        
        # Consistent gain for MAX98357A (-2.0dB = Goldilocks)
        VOL_GAIN = -2.0
        
        sentence_count = 0
        
        # [WARM START] Synthesize a dot to initialize the ESP32 buffers immediately
        try:
            print(f"DEBUG: [Stream] Triggering Warm Start...")
            warm_audio = await tts.synthesize_stream(".", volume_gain_db=VOL_GAIN)
            if warm_audio:
                yield warm_audio
                sentence_count += 1
        except Exception as e:
            print(f"ERROR: [Stream] Warm start failed: {e}")

        while True:
            item = await streaming_manager.get(convo_id)
            if item is None:
                break
                
            if item["type"] == "sentence":
                text = item["text"]
                print(f"DEBUG: [Stream] Synthesizing sentence #{sentence_count}: {text[:30]}...")
                
                try:
                    audio_bytes = await tts.synthesize_stream(text, volume_gain_db=VOL_GAIN)
                    if audio_bytes:
                        # For the first sentence, we send the whole thing (with header)
                        # For subsequent sentences, we strip the header for seamless joining
                        if sentence_count > 0:
                            audio_bytes = strip_mp3_header(audio_bytes)
                        
                        yield audio_bytes
                        sentence_count += 1
                        
                except Exception as e:
                    print(f"ERROR: [Stream] Synthesis failed for sentence: {e}")
            
            elif item["type"] == "metadata":
                # Handle mood changes if needed (e.g., push to socket)
                pass

        # Cleanup
        streaming_manager.cleanup(convo_id)
        print(f"DEBUG: [Stream] Conversation {convo_id} completed.")

    return StreamingResponse(audio_stream_generator(), media_type="audio/mpeg")

@app.get("/v1/history")
async def get_history(device_id: str, session: Session = Depends(get_session)):
    statement = select(Conversation).where(Conversation.device_id == device_id).order_by(Conversation.timestamp.desc()).limit(10)
    return session.exec(statement).all()

@app.get("/v1/device/{device_id}/poll")
async def poll_device(device_id: str, session: Session = Depends(get_session)):
    """
    Endpoint for the ESP32 to poll for pending alerts or responses.
    """
    # Look for very recent high-priority alerts (remote triggers)
    one_min_ago = datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=1)
    statement = select(SensorReading).where(
        SensorReading.device_id == device_id,
        SensorReading.timestamp >= one_min_ago,
        or_(
            SensorReading.event == "remote_simulator_alert",
            SensorReading.event == "low_moisture_alert"
        )
    ).order_by(SensorReading.timestamp.desc())
    
    alert = session.exec(statement).first()
    
    if alert:
        print(f"🔔 [POLL] Found Alert for {device_id}: {alert.event}")
        # Map physical alert to the correct sound
        sound_type = "low-moisture" if "moisture" in (alert.event or "") else "general"
        return {
            "has_alert": True,
            "event": alert.event,
            "audio_url": f"/v1/audio/notification/{sound_type}"
        }
    
    return {"has_alert": False}

@app.get("/v1/audio/notification/{alert_type}")
async def get_notification_audio(alert_type: str):
    """Returns a short notification ping/alert sound."""
    settings = get_settings()
    # Simple logic to return different pings
    filename = "hmm.mp3" # Default
    if "moisture" in alert_type:
        filename = "hmm.mp3" # We use hmm.mp3 as the standard alert for now
        
    return FileResponse(os.path.join(settings.STORAGE_PATH, filename))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
