import os
from datetime import datetime, UTC
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Header, UploadFile, File, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from sqlmodel import Session, select
from models import init_db, get_engine, Conversation, Device, SensorReading
from config import get_settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database on startup
    init_db()
    
    # Ensure storage paths exist
    settings = get_settings()
    backchannel_dir = os.path.join(settings.STORAGE_PATH, "backchannels")
    os.makedirs(backchannel_dir, exist_ok=True)
    os.makedirs(settings.STORAGE_PATH, exist_ok=True)

    # Pre-generate "Hmm" backchannel if missing (Crucial for low-latency header delivery)
    hmm_path = os.path.join(backchannel_dir, "hmm.mp3")
    if not os.path.exists(hmm_path):
        print("DEBUG: Generating warm-up audio (hmm.mp3)...")
        from services.speech_synthesis import SpeechSynthesisService
        tts = SpeechSynthesisService()
        try:
            # We use a slightly longer pause to buffer the stream
            await tts.synthesize("Hmm...", hmm_path) 
            print("DEBUG: hmm.mp3 generated successfully.")
        except Exception as e:
            print(f"WARNING: Could not generate hmm.mp3: {e}")

    yield

app = FastAPI(title="Smart Plant Pot Backend", lifespan=lifespan)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for simulator and audio data
app.mount("/simulator", StaticFiles(directory="simulator"), name="simulator")
app.mount("/audio", StaticFiles(directory="audio_artifacts"), name="audio")

def get_session():
    with Session(get_engine()) as session:
        yield session


@app.get("/health")
def health_check():
    return {"status": "healthy"}

from agents.orchestrator import create_pot_graph
from services.transcription import TranscriptionService
from services.speech_synthesis import SpeechSynthesisService

async def archive_conversation_task(device_id: str, transcription: str, ai_response: str):
    """Background task to archive conversation and synthesize a full audio file."""
    from models import get_engine, Conversation
    from services.speech_synthesis import SpeechSynthesisService
    from sqlmodel import Session
    import os
    from datetime import datetime
    from config import get_settings # Import get_settings here for background task scope
    
    settings = get_settings()
    tts = SpeechSynthesisService()
    
    try:
        # Synthesis for archival file
        full_audio = await tts.synthesize_stream(ai_response)
        filename = f"reco_{device_id}_{int(datetime.now().timestamp())}.mp3"
        save_path = os.path.join(settings.STORAGE_PATH, filename)
        
        with open(save_path, "wb") as f:
            f.write(full_audio)
            
        with Session(get_engine()) as session:
            convo = Conversation(
                device_id=device_id,
                transcription=transcription,
                ai_response=ai_response,
                audio_file_path=filename
            )
            session.add(convo)
            session.commit()
        print(f"DEBUG: Archived conversation for {device_id}")
    except Exception as e:
        print(f"DEBUG: Archiver failed: {e}")

@app.get("/v1/audio/stream/{convo_id}")
async def stream_audio(convo_id: int, session: Session = Depends(get_session)):
    convo = session.get(Conversation, convo_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    async def audio_stream_generator():
        import asyncio
        import re
        tts = SpeechSynthesisService()
        
        # Audio gain adjustment (-1.5dB for clarity without loudness loss)
        VOL_GAIN = -1.5
        CHUNK_SIZE = 4096 # Slightly larger chunks for better throughput
        
        reply_text = convo.ai_response or ""
        sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', reply_text) if s.strip()]
        print(f"DEBUG: Found {len(sentences)} sentences to synthesize.")
        
        queue = asyncio.Queue(maxsize=3)

        async def producer():
            """Synthesizes sentences in the background."""
            try:
                for i, sentence in enumerate(sentences):
                    # Add a small text tail to ensure the TTS generates enough audio/silence at the end 
                    # to prevent the ESP32 decoder from cutting off the last words.
                    padded_sentence = f"{sentence} . . ."
                    print(f"DEBUG: [Producer] Synthesizing sentence {i+1}/{len(sentences)}: {sentence[:30]}...")
                    audio = await tts.synthesize_stream(padded_sentence, volume_gain_db=VOL_GAIN)
                    if audio:
                        print(f"DEBUG: [Producer] Sentence {i+1} synthesized successfully ({len(audio)} bytes).")
                        await queue.put(audio)
                    else:
                        print(f"DEBUG: [Producer] Sentence {i+1} returned NO AUDIO.")
            except Exception as e:
                print(f"ERROR: [Producer] Failed during synthesis: {e}")
            finally:
                print("DEBUG: [Producer] Putting sentinel None into queue.")
                await queue.put(None)

        # START SYNTHESIS IMMEDIATELY (Concurrent with backchannel)
        producer_task = asyncio.create_task(producer())

        try:
            # 1. Sentences from Queue
            while True:
                print("DEBUG: [Streamer] Waiting for audio/sentinel from queue...")
                audio = await queue.get()
                if audio is None:
                    print("DEBUG: [Streamer] Sentinel received. Ending stream.")
                    break
                
                print(f"DEBUG: [Streamer] Yielding sentence in {CHUNK_SIZE}b chunks")
                for i in range(0, len(audio), CHUNK_SIZE):
                    yield audio[i:i + CHUNK_SIZE]
                    await asyncio.sleep(0.01) 
                
                # Small pause between synthesized sentences to help the hardware decoder sync
                await asyncio.sleep(0.1) 
            
            # 3. Final Flush (Ensures the ESP32 consumes the very last bits of data)
            print("DEBUG: [Streamer] Final flush.")
            yield b"\x00" * 2048
            await asyncio.sleep(0.5)

        except Exception as e:
            print(f"ERROR: [Streamer] Stream interrupted: {e}")
        finally:
            print("DEBUG: [Streamer] Cleaning up producer task.")
            producer_task.cancel()

    from fastapi.responses import StreamingResponse
    return StreamingResponse(audio_stream_generator(), media_type="audio/mpeg")

@app.post("/v1/ingest")
async def ingest_data(
    device_id: str,
    temperature: float,
    moisture: float,
    light: float,
    background_tasks: BackgroundTasks,
    user_query: Optional[str] = Query(None),
    event: Optional[str] = None,
    audio: Optional[UploadFile] = File(None),
    session: Session = Depends(get_session)
):
    print(f"DEBUG: Received Ingest - Device: {device_id}, Text: {user_query}, Audio: {audio.filename if audio else 'None'}")
    # 1. Ensure device exists
    device = session.get(Device, device_id)
    if not device:
        device = Device(id=device_id, name=f"Pot {device_id}", species="Basil")
        session.add(device)
        session.commit()
    
    # 2. Save sensor reading
    reading = SensorReading(device_id=device_id, temperature=temperature, moisture=moisture, light=light, event=event)
    session.add(reading)
    
    # 3. Handle STT
    is_silent_recording = False
    if not user_query and audio:
        from services.storage import StorageService
        storage = StorageService()
        audio_path = await storage.save_audio(audio, device_id)
        stt = TranscriptionService()
        try:
            user_query = await stt.transcribe(audio_path)
            if not user_query:
                is_silent_recording = True
        except Exception:
            user_query = ""
            is_silent_recording = True
    
    settings = get_settings()
    if event == "wake_word" and not user_query:
        user_query = settings.WAKE_WORD
        is_silent_recording = False # Override if it's just the wake word
    
    # 4. Define High-Speed Dispatcher & Knowledge Logic
    # (Removed duplicated code for brevity, logic remains the same)
    from agents.orchestrator import fast_find_knowledge
    keywords_sensors = [
        "light", "moisture", "water", "temperature", "temp", "hungry", "health", 
        "care", "how are you", "routine", "advice", "habitat", "potting", "fertilizer"
    ]
    query_text = (user_query or "").lower()
    is_sensor_query = any(k in query_text for k in keywords_sensors)
    local_knowledge = fast_find_knowledge(device.species) if (user_query and len(user_query) > 3) else None

    # 5. Handle Response Generation
    if is_silent_recording:
        reply_text = "Hi there, I didn't catch what you said. Could you repeat that?"
        mood = "neutral"
        priority = "normal"
    else:
        # Run Agent IMMEDIATELY for text display
        from agents.conversation_agent import ConversationAgent
        agent = ConversationAgent()
        
        sensor_text = f"Temp: {temperature}, Moisture: {moisture}, Light: {light}" if is_sensor_query else "Not requested."
        know_text = f"{local_knowledge.biological_info} {local_knowledge.care_tips}" if local_knowledge else "No local data found."

        state = {
            "device_id": device_id,
            "species": device.species,
            "user_query": user_query or "Hello",
            "sensor_analysis": sensor_text,
            "plant_knowledge": know_text,
            "sensor_data": {"temperature": temperature, "moisture": moisture, "light": light}
        }
        
        result = await agent.run(state)
        reply_text = result.get("conversation_response", "")
        mood = result.get("mood", "neutral")
        priority = result.get("priority", "normal")

    # 6. Create Conversation Record with full text
    convo = Conversation(
        device_id=device_id,
        transcription=user_query,
        ai_response=reply_text,
        mood=mood
    )
    session.add(convo)
    session.commit()
    session.refresh(convo)

    # 7. Return Full JSON
    from fastapi import Response
    import json
    content = {
        "user_query": user_query,
        "reply_text": reply_text,
        "audio_url": f"/v1/audio/stream/{convo.id}",
        "display": {
            "mood": mood,
            "priority": priority
        },
        "id": convo.id
    }
    return Response(content=json.dumps(content), media_type="application/json", headers={"Connection": "close"})


@app.get("/v1/history")
async def get_history(device_id: str = "pot_simulator_001", session: Session = Depends(get_session)):
    statement = select(Conversation).where(Conversation.device_id == device_id).order_by(Conversation.timestamp.desc()).limit(10)
    results = session.exec(statement).all()
    
    # Format for frontend
    history = []
    for c in results:
        history.append({
            "id": c.id,
            "user_query": c.transcription,
            "reply_text": c.ai_response,
            "mood": c.mood,
            "audio_url": f"/audio/{c.audio_file_path}" if c.audio_file_path else None,
            "timestamp": c.timestamp.isoformat()
        })
    return history

@app.get("/v1/audio/{convo_id}")
async def get_audio(convo_id: int, session: Session = Depends(get_session)):
    convo = session.get(Conversation, convo_id)
    if not convo or not convo.audio_file_path:
        raise HTTPException(status_code=404, detail="Audio not found")
    
    settings = get_settings()
    full_path = os.path.join(settings.STORAGE_PATH, convo.audio_file_path)
    return FileResponse(full_path, media_type="audio/wav")

@app.post("/v1/device/{device_id}/species")
async def update_species(
    device_id: str, 
    species: str, 
    session: Session = Depends(get_session)
):
    """Updates the plant species for a specific device."""
    device = session.get(Device, device_id)
    if not device:
        device = Device(id=device_id, name=f"Pot {device_id}", species=species)
        session.add(device)
    else:
        device.species = species
    
    session.commit()
    return {"status": "updated", "species": species}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
