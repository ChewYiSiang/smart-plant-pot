import os
import whisper
import torch
from ..config import get_settings

class TranscriptionService:
    def __init__(self):
        self.settings = get_settings()
        # Use "base" or "tiny" for lower resource usage on local machines
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = whisper.load_model("base", device=self.device)

    async def transcribe(self, audio_file_path: str) -> str:
        """Transcribes audio file to text using local Whisper model."""
        if not os.path.exists(audio_file_path):
            return ""
            
        # whisper.transcribe is a synchronous call, in a high-traffic app 
        # you might want to run this in a threadpool
        result = self.model.transcribe(audio_file_path)
        return result["text"].strip()
