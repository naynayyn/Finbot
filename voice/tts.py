import asyncio
import edge_tts

VOICE = "en-US-JennyNeural"

async def speak_async(text: str, output_path: str = "response.mp3"):
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output_path)

def speak(text: str, output_path: str = "response.mp3"):
    asyncio.run(speak_async(text, output_path))
