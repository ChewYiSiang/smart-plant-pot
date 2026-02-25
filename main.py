import os
from datetime import datetime, timedelta, UTC
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Header, UploadFile, File, Query, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from sqlmodel import Session, select, or_
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
    """Streams the entire audio response in ONE SHOT to ensure header integrity."""
    convo = session.get(Conversation, convo_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    async def audio_stream_generator():
        import asyncio
        tts = SpeechSynthesisService()

        # [MODIFIED] -2.0dB - The "Goldilocks" middle ground between too soft and muffled
        VOL_GAIN = -2.0

        reply_text = convo.ai_response or ""
        if not reply_text.strip():
            print("WARNING: [Stream] Nothing to synthesize.")
            return

        print(f"DEBUG: [Stream] One-Shot Synthesis for Convo {convo_id}: {reply_text[:50]}...")

        try:
            # [ONE-SHOT] Synthesize the entire response at once.
            # This ensures only ONE MP3 header is sent, eliminating transition static.
            audio = await tts.synthesize_stream(reply_text, volume_gain_db=VOL_GAIN)

            if audio:
                print(f"DEBUG: [Stream] Synthesis complete. Delivering {len(audio)} bytes.")
                # Yield in chunks for network stability
                CHUNK_SIZE = 8192
                for i in range(0, len(audio), CHUNK_SIZE):
                    yield audio[i : i + CHUNK_SIZE]
                    await asyncio.sleep(0.01) # Yield control
            else:
                print("ERROR: [Stream] Synthesis returned NO AUDIO.")

        except Exception as e:
            print(f"ERROR: [Stream] Failed during one-shot synthesis: {e}")

    return StreamingResponse(audio_stream_generator(), media_type="audio/mpeg")

@app.post("/v1/ingest")
async def ingest_data(
    device_id: str,
    temperature: float,
    moisture: float,
    light: float,
    event: Optional[str] = None,
    user_query: Optional[str] = Query(None),
    audio: Optional[UploadFile] = File(None),
    session: Session = Depends(get_session)
):
    print(f"\n🚀 [INGEST START] Device: {device_id}, Event: {event}, Text: {user_query}")
    # 1. Ensure device exists
    device = session.get(Device, device_id)
    if not device:
        is_sim = (device_id == "pot_simulator_001" or "sim" in device_id.lower())
        device = Device(id=device_id, name=f"Pot {device_id}", species="Basil", is_simulator=is_sim)
        session.add(device)
        session.commit()

    # 0. Handle Sensor Data Prioritization (Physical Pot vs Simulator)
    used_hardware_data = False
    if getattr(device, "is_simulator", False):
        ten_mins_ago = datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=10)

        # Look for the most recent reading from ANY hardware device (is_simulator=False)
        # We join with device to check is_simulator flag
        statement = (
            select(SensorReading)
            .join(Device)
            .where(
                Device.is_simulator == False,
                SensorReading.timestamp >= ten_mins_ago
            )
            .order_by(SensorReading.timestamp.desc())
            .limit(1)
        )

        recent_reading = session.exec(statement).first()
        if recent_reading:
            hw_device_id = getattr(recent_reading, "device_id", "Unknown")
            print(f"DEBUG: Found recent hardware reading from {hw_device_id}. Overriding simulator sliders.")

            # Prioritize Hardware data if present
            temperature = getattr(recent_reading, "temperature", temperature)
            light = getattr(recent_reading, "light", light)

            # Special logic for moisture: If hardware sensor says 0 (likely disconnected),
            # fall back to simulator value so user can still test the flow.
            hw_moisture = getattr(recent_reading, "moisture", 0.0)
            if hw_moisture > 0.0:
                print(f"  ℹ  Prioritizing hardware moisture: {hw_moisture}%")
                moisture = hw_moisture
            else:
                print(f"  ⚠  Hardware moisture is 0% (disconnected?). Falling back to simulator slider: {moisture}%")       

            used_hardware_data = True

    # This is for testing with the simulator button even if real sensors are high.
    force_notification = (event == "low_moisture_alert")

    # 1. Log Raw Data for Verification
    source_label = "[LIVE SENSORS]" if not getattr(device, "is_simulator", False) else "[SIMULATOR]"
    if used_hardware_data:
        source_label = "[SIMULATOR + HW OVERRIDE]"

    print(f"\n--- [INGEST] {source_label} Source: {device_id} ---")
    if used_hardware_data:
        print(f"  ℹ  Using live data from physical pot (s3_devkitc_plant_pot)")
    print(f"  🌡 Temperature: {temperature:.1f}°C")
    print(f"  💧 Moisture:    {moisture:.1f}%")
    print(f"  ☀ Light:       {light:.1f}%")
    print(f"  ✨ Event:       {event or 'None'}")
    print(f"-----------------------------------\n")

    # 1. Create Sensor Reading Record
    try:
        reading = SensorReading(device_id=device_id, temperature=temperature, moisture=moisture, light=light, event=event)  
        session.add(reading)

        # --- REMOTE TRIGGER: Propagation from Simulator to Physical Pot ---
        if force_notification and getattr(device, "is_simulator", False):
            # Find any physical device that has sent data in the last 10 minutes
            ten_mins_ago = datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=10)
            statement = (
                select(Device)
                .join(SensorReading)
                .where(
                    Device.is_simulator == False,
                    SensorReading.timestamp >= ten_mins_ago
                )
                .order_by(SensorReading.timestamp.desc())
                .limit(1)
            )
            # Find the physical device the user is actually using
            physical_device = session.get(Device, "s3_devkitc_plant_pot")
            
            # If not found, fall back to any active hardware device
            if not physical_device:
                physical_device = session.exec(statement).first()
            
            # Last resort: find ANY physical device
            if not physical_device:
                physical_device = session.exec(select(Device).where(Device.is_simulator == False).limit(1)).first()

            if physical_device:
                # Propagation: Add reading directly for the physical device
                session.add(SensorReading(
                    device_id=physical_device.id,
                    temperature=temperature,
                    moisture=10.0,
                    light=light,
                    event="remote_simulator_alert"
                ))
                print(f"✅ [TRACE] Alert propagated to {physical_device.id}")
            else:
                print(f"🔍 [TRACE] No physical devices found to propagate alert to.")

        session.commit()
        print(f"💾 [TRACE] Session Committed successfully.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"WARNING: Could not log sensor reading: {e}")

    # 3. Handle STT (Only if user_query not provided)
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
    # --- [REFINED] EVENT-ONLY INGEST LOGIC ---
    # If this is just a sensor log or an alert event (no voice/text query),
    # skip the AI agent and return a minimalist response.
    if not (user_query or audio):
        reply_text = "..." # Minimalist placeholder
        mood = "neutral"
        priority = "normal"
    elif is_silent_recording:
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

    # 6. Create Conversation Record with full text (SKIP IF SILENT)
    class MockConvo:
        def __init__(self, id=0):
            self.id = id
            self.reply_text = "..."
            self.mood = "neutral"

    convo = None
    if reply_text != "...":
        try:
            convo = Conversation(
                device_id=device_id,
                transcription=user_query,
                ai_response=reply_text,
                mood=mood
            )
            session.add(convo)
            session.commit()
            session.refresh(convo)
        except Exception as e:
            print(f"WARNING: Failed to save conversation to DB: {e}")
            convo = MockConvo()
    else:
        # It's a silent event, just create a mock object for the response
        convo = MockConvo(id=9999)

    # 7. Return Full JSON

    # 7. Return Full JSON
    from fastapi import Response
    import json

    notification_url = None
    if moisture < 20.0 or force_notification:
        notification_url = "/v1/audio/notification/low-moisture"

    content = {
        "user_query": user_query,
        "reply_text": reply_text,
        "audio_url": f"/v1/audio/stream/{convo.id}" if convo.id != 9999 else None,
        "notification_url": notification_url,
        "display": {
            "mood": mood,
            "priority": priority
        },
        "id": convo.id
    }
    # 8. Flag Physical Device for Audio if this is a simulator query
    # The user wants simulator queries to play on the physical speaker as a backup.
    if device_id == "pot_simulator_001":
        # Target the physical device (s3_devkitc_plant_pot)
        physical_device = session.get(Device, "s3_devkitc_plant_pot")
        # ONLY flag if this is a real vocal response (not the silent 9999 ghost ID)
        if physical_device and convo.id != 9999:
            physical_device.pending_audio_id = convo.id
            session.add(physical_device)
            session.commit()
            print(f"DEBUG: Flagged physical device 's3_devkitc_plant_pot' with pending audio {convo.id}")

    return Response(content=json.dumps(content), media_type="application/json", headers={"Connection": "close"})

@app.get("/v1/device/{device_id}/poll")
async def poll_for_audio(device_id: str, session: Session = Depends(get_session)):
    """Polling endpoint for the ESP32 to check for pending audio streams."""
    print(f"DEBUG: [Poll Request] From Device: {device_id}")

    device = session.get(Device, device_id)
    # 0. Register device if it doesn't exist yet
    if not device:
        print(f"  ℹ [Poll] New device identified: {device_id}. Registering...")
        is_sim = (device_id == "pot_simulator_001" or "sim" in device_id.lower())
        device = Device(id=device_id, name=f"Pot {device_id}", species="Basil", is_simulator=is_sim)
        session.add(device)
        session.commit()
        session.refresh(device)

    convo_id = None
    if device.pending_audio_id is not None:
        convo_id = device.pending_audio_id
        print(f"  🔔 [Poll] PENDING VOICE ID: {convo_id} for device {device_id}")
        # Clear the flag immediately after serving
        device.pending_audio_id = None
        session.add(device)
        session.commit()

    # 2. Check for Low Moisture Notification
    one_hour_ago = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=1)

    # Query only for the most recent alert event within the window
    statement = (
        select(SensorReading)
        .where(
            SensorReading.device_id == device_id,
            SensorReading.timestamp >= one_hour_ago,
            or_(
                SensorReading.moisture < 20.0,
                SensorReading.event.in_(["low_moisture_alert", "remote_simulator_alert"])
            )
        )
        .order_by(SensorReading.timestamp.desc())
        .limit(1)
    )

    last_reading = session.exec(statement).first()
    notification_url = None
    notification_format = None
    if last_reading:
        # [NEW] Check if this alert has already been played on this device
        if device.last_notified_reading_id != last_reading.id:
            print(f"  ⚠ [Poll] NEW ALERT found (ID: {last_reading.id}, Event: {last_reading.event}) for {device_id}")       
            notification_url = "/v1/audio/notification/low-moisture"

            # Detect format (WAV or MP3)
            folder = "audio_artifacts/notification_sound"
            if os.path.exists(folder):
                files = [f for f in os.listdir(folder) if f.lower().endswith((".wav", ".mp3"))]
                if any(f.lower().endswith(".wav") for f in files):
                    notification_format = "wav"
                elif any(f.lower().endswith(".mp3") for f in files):
                    notification_format = "mp3"

            # Consume the alert
            device.last_notified_reading_id = last_reading.id
            session.add(device)
            session.commit()
        else:
            print(f"  ℹ [Poll] Skipping already played alert (ID: {last_reading.id}) for {device_id}")

    if not convo_id and not notification_url:
        print(f"  💤 [Poll] No pending audio/alerts for {device_id}")

    return {
        "convo_id": convo_id,
        "audio_url": f"/v1/audio/stream/{convo_id}" if convo_id else None,
        "notification_url": notification_url,
        "notification_format": notification_format
    }

def serve_notification_sound(filename_prefix: str, default_priority_exts: list = [".wav", ".mp3"]):
    folder = "audio_artifacts/notification_sound"
    if not os.path.exists(folder):
        raise HTTPException(status_code=404, detail="Notification folder missing")

    valid_exts = (".wav", ".mp3")
    files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f)) and f.lower().endswith(valid_exts)]   

    # Try prioritized extensions for the specific prefix
    for ext in default_priority_exts:
        target = f"{filename_prefix}{ext}"
        if target in files:
            file_path = os.path.join(folder, target)
            print(f"  ✅ [Serving] Delivering prioritized file: {file_path}")
            media_type = "audio/wav" if ext == ".wav" else "audio/mpeg"
            return FileResponse(file_path, media_type=media_type)

    # Fallback to any file with that prefix if priority failed
    for f in files:
        if f.lower().startswith(filename_prefix):
            file_path = os.path.join(folder, f)
            print(f"  ✅ [Serving] Delivering fallback file: {file_path}")
            media_type = "audio/wav" if f.lower().endswith(".wav") else "audio/mpeg"
            return FileResponse(file_path, media_type=media_type)

    raise HTTPException(status_code=404, detail=f"No audio file found for {filename_prefix}")

@app.get("/v1/audio/notification/low-moisture")
async def get_low_moisture_notification():
    """Serves the low moisture notification sound (priority: alert.wav)."""
    return serve_notification_sound("alert")

@app.get("/v1/audio/notification/record-start")
async def get_record_start_notification():
    """Serves the record start sound (priority: record_start.wav)."""
    return serve_notification_sound("record_start")

@app.get("/v1/audio/notification/record-stop")
async def get_record_stop_notification():
    """Serves the record stop sound (priority: record_stop.wav)."""
    return serve_notification_sound("record_stop")
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