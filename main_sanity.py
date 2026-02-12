from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
import uvicorn
import time
import os

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/v1/ingest")
async def ingest(user_query: str = Query(...)):
    print(f"DEBUG: Received {user_query}")
    def generator():
        # Minimal WAV header
        yield b'RIFF' + b'\xff\xff\xff\xff' + b'WAVEfmt ' + b'\x10\x00\x00\x00\x01\x00\x01\x00\x80\x3e\x00\x00\x00\x7d\x00\x00\x02\x00\x10\x00data' + b'\xff\xff\xff\xff'
        for i in range(5):
            print(f"DEBUG: Yielding chunk {i}")
            yield b'\x00' * 1600 # 50ms of silence
            time.sleep(0.5)
    return StreamingResponse(generator(), media_type="audio/wav")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
