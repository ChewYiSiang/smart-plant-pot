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
    # Ensure storage path exists
    settings = get_settings()
    if not os.path.exists(settings.STORAGE_PATH):
        os.makedirs(settings.STORAGE_PATH)
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
        filename = f"reco_{device_id}_{int(datetime.now().timestamp())}.wav"
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
async def stream_audio(convo_id: int, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    convo = session.get(Conversation, convo_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    device = session.get(Device, convo.device_id)
    settings = get_settings()
    
    # We need to find the latest sensors and knowledge to pass to the agent
    # In a real app, we'd store the state in the Conversation record.
    # For now, we'll fetch the latest for the device.
    from models import SensorReading
    statement = select(SensorReading).where(SensorReading.device_id == convo.device_id).order_by(SensorReading.timestamp.desc())
    reading = session.exec(statement).first()
    
    from agents.orchestrator import fast_find_knowledge
    keywords_sensors = ["light", "moisture", "water", "temperature", "temp", "hungry", "health", "care", "how are you"]
    query_text = (convo.transcription or "").lower()
    is_sensor_query = any(k in query_text for k in keywords_sensors)
    local_knowledge = fast_find_knowledge(device.species) if (convo.transcription and len(convo.transcription) > 3) else None

    async def audio_stream_generator():
        import struct
        def get_wav_header():
            return struct.pack('<4sI4s4sIHHIIHH4sI', b'RIFF', 0xFFFFFFFF, b'WAVE', b'fmt ', 16, 1, 1, 16000, 32000, 2, 16, b'data', 0xFFFFFFFF)
        
        def strip_wav_header(data: bytes) -> bytes:
            d_idx = data.find(b'data')
            return data[d_idx+8:] if d_idx != -1 else data[44:]

        yield get_wav_header()
        tts = SpeechSynthesisService()
        
        # 1. IMMEDIATE BACKCHANNEL
        if not is_sensor_query or (local_knowledge and len(local_knowledge.biological_info) > 100):
            backchannel_dir = os.path.join("audio_artifacts", "backchannels")
            hmm_path = os.path.join(backchannel_dir, "hmm.wav")
            if os.path.exists(hmm_path):
                with open(hmm_path, "rb") as f:
                    f.seek(44)
                    yield f.read()
            else:
                yield strip_wav_header(await tts.synthesize_stream("Hmm..."))

        # 2. STREAM PRE-GENERATED REPLY
        reply_text = convo.ai_response or ""
        
        import re
        sentences = re.split(r'(?<=[.!?]) +', reply_text)
        for sentence in sentences:
            if sentence.strip():
                yield strip_wav_header(await tts.synthesize_stream(sentence))

    from fastapi.responses import StreamingResponse
    return StreamingResponse(audio_stream_generator(), media_type="audio/wav")


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
    
    # 4. Define High-Speed Dispatcher & Knowledge Logic
    from agents.orchestrator import fast_find_knowledge
    keywords_sensors = [
        "light", "moisture", "water", "temperature", "temp", "hungry", "health", 
        "care", "how are you", "routine", "advice", "habitat", "potting", "fertilizer"
    ]
    query_text = (user_query or "").lower()
    is_sensor_query = any(k in query_text for k in keywords_sensors)
    local_knowledge = fast_find_knowledge(device.species) if (user_query and len(user_query) > 3) else None

    # 5. Run Agent IMMEDIATELY for text display
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
    return {
        "user_query": user_query,
        "reply_text": reply_text,
        "audio_url": f"/v1/audio/stream/{convo.id}",
        "display": {
            "mood": mood,
            "priority": priority
        },
        "id": convo.id
    }


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
