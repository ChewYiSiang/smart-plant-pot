import os
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Header, UploadFile, File
from fastapi.responses import JSONResponse
from sqlmodel import Session
from .models import init_db, get_engine
from .config import get_settings

app = FastAPI(title="Smart Plant Pot Backend")

# Initialize database on startup
@app.on_event("startup")
def on_startup():
    init_db()
    # Ensure storage path exists
    settings = get_settings()
    if not os.path.exists(settings.STORAGE_PATH):
        os.makedirs(settings.STORAGE_PATH)

def get_session():
    with Session(get_engine()) as session:
        yield session

async def verify_api_key(x_api_key: str = Header(...)):
    settings = get_settings()
    if x_api_key != settings.DEVICE_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return x_api_key

@app.get("/health")
def health_check():
    return {"status": "healthy"}

from .agents.orchestrator import create_pot_graph
from .services.transcription import TranscriptionService
from .services.speech_synthesis import SpeechSynthesisService
from .models import Conversation

@app.post("/v1/ingest", dependencies=[Depends(verify_api_key)])
async def ingest_data(
    device_id: str,
    temperature: float,
    moisture: float,
    light: float,
    event: Optional[str] = None,
    audio: Optional[UploadFile] = File(None),
    session: Session = Depends(get_session)
):
    # 1. Ensure device exists
    device = session.get(Device, device_id)
    if not device:
        device = Device(id=device_id, name=f"Pot {device_id}", species="Basil") # Defaulting to Basil
        session.add(device)
        session.commit()
    
    # 2. Save sensor reading
    reading = SensorReading(
        device_id=device_id,
        temperature=temperature,
        moisture=moisture,
        light=light,
        event=event
    )
    session.add(reading)
    
    # 3. Handle Audio -> STT
    user_query = None
    if audio:
        storage = StorageService()
        audio_path = await storage.save_audio(audio, device_id)
        
        stt = TranscriptionService()
        user_query = await stt.transcribe(audio_path)
    
    # 4. Trigger Multi-Agent Flow
    graph = create_pot_graph()
    initial_state = {
        "device_id": device_id,
        "user_query": user_query,
        "sensor_data": {
            "temperature": temperature,
            "moisture": moisture,
            "light": light
        }
    }
    
    final_output = graph.invoke(initial_state)
    
    # 5. Generate Response TTS
    settings = get_settings()
    output_audio_name = f"response_{int(datetime.utcnow().timestamp())}.wav"
    output_audio_path = os.path.join(settings.STORAGE_PATH, device_id, "responses", output_audio_name)
    
    tts = SpeechSynthesisService()
    await tts.synthesize(final_output["reply_text"], output_audio_path)
    
    # 6. Save Conversation Record
    convo = Conversation(
        device_id=device_id,
        transcription=user_query,
        ai_response=final_output["reply_text"],
        mood=final_output["mood"],
        audio_file_path=os.path.join(device_id, "responses", output_audio_name)
    )
    session.add(convo)
    session.commit()
    
    return {
        "reply_text": final_output["reply_text"],
        "audio_url": f"/v1/audio/{convo.id}", # Endpoint to serve the file
        "display": {
            "mood": final_output["mood"],
            "icons": final_output["icons"],
            "priority": final_output["priority"]
        }
    }

from fastapi.responses import FileResponse

@app.get("/v1/audio/{convo_id}")
async def get_audio(convo_id: int, session: Session = Depends(get_session)):
    convo = session.get(Conversation, convo_id)
    if not convo or not convo.audio_file_path:
        raise HTTPException(status_code=404, detail="Audio not found")
    
    settings = get_settings()
    full_path = os.path.join(settings.STORAGE_PATH, convo.audio_file_path)
    return FileResponse(full_path, media_type="audio/wav")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
