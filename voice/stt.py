import os
import groq
from dotenv import load_dotenv

load_dotenv()
client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))

def transcribe_audio(audio_file_path: str) -> dict:
    """Transcribe audio and detect language. Returns {text, language}"""
    with open(audio_file_path, "rb") as f:
        response = client.audio.transcriptions.create(
            file=f,
            model="whisper-large-v3",
            response_format="verbose_json"
        )
    return {
        "text": response.text,
        "language": response.language
    }
