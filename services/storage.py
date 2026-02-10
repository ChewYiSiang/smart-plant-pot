import os
import aiofiles
from fastapi import UploadFile
from config import get_settings

class StorageService:
    def __init__(self):
        self.settings = get_settings()
        self.base_path = self.settings.STORAGE_PATH

    async def save_audio(self, file: UploadFile, device_id: str) -> str:
        """Saves an uploaded audio file and returns the file path."""
        # Create device-specific folder
        device_dir = os.path.join(self.base_path, device_id, "uploads")
        os.makedirs(device_dir, exist_ok=True)
        
        # Create unique filename
        filename = f"{int(os.path.getmtime(self.base_path) * 1000)}.wav" # Placeholder for better naming
        # Actually use timestamp + original extension
        import time
        timestamp = int(time.time())
        extension = file.filename.split(".")[-1] if file.filename else "wav"
        filename = f"{timestamp}.{extension}"
        
        file_path = os.path.join(device_dir, filename)
        
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
            
        return file_path

    async def get_audio_path(self, relative_path: str) -> str:
        return os.path.join(self.base_path, relative_path)
