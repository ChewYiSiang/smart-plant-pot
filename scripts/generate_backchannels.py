import asyncio
import os
from services.speech_synthesis import SpeechSynthesisService

async def generate_backchannels():
    service = SpeechSynthesisService()
    backchannels = {
        "hmm": "Hmm...",
        "let_me_see": "Let me see...",
        "interesting": "That's interesting...",
        "one_moment": "One moment..."
    }
    
    output_dir = "audio_artifacts/backchannels"
    os.makedirs(output_dir, exist_ok=True)
    
    for name, text in backchannels.items():
        print(f"Generating {name}...")
        path = os.path.join(output_dir, f"{name}.wav")
        await service.synthesize(text, path)
        print(f"Saved to {path}")

if __name__ == "__main__":
    asyncio.run(generate_backchannels())
