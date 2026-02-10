# Smart Plant Pot Backend

A voice-enabled IoT backend for an ESP32-powered smart plant pot. Powered by FastAPI, LangGraph, and self-hosted Whisper.

## Features
- **Multi-Agent AI**: Specialized agents for sensor analysis, plant knowledge, and conversation.
- **Local Speech-to-Text**: Privacy-focused transcription using OpenAI Whisper (running locally).
- **IoT Integration**: Structured JSON + Audio response flow designed for microcontroller constraints.

## Prerequisites
- Python 3.9+
- [FFmpeg](https://ffmpeg.org/download.html) (Required for local Whisper)
- API Keys: Google Gemini (for LLM and TTS patterns)

## Setup

1. **Clone and Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   Copy `.env.example` to `.env` and fill in your API keys.
   ```bash
   cp .env.example .env
   ```

3. **Database Initialization**
   The database (SQLite by default) will be automatically created on the first run.

## Running the Server
```bash
python main.py
# or
uvicorn main:app --reload
```

## Testing & Simulation

### 1. Manual Simulation
To simulate a device sending sensor data and a voice query:
```bash
python tests/simulate_device.py
```
*Note: Ensure you have a `tests/sample_query.wav` file for the audio simulation.*

### 2. Service-level Tests
To test the STT and TTS services in isolation:
```bash
python tests/test_services.py
```

## Project Structure
- `agents/`: LangGraph orchestration and individual AI agents.
- `services/`: STT, TTS, and storage management.
- `models.py`: Database schemas.
- `main.py`: FastAPI endpoints and integration.
- `audio_artifacts/`: Local storage for voice recordings and responses.
