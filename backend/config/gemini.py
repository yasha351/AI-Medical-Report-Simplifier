import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

def get_gemini_client():
    api_key = os.environ.get("AQ.Ab8RN6KqMqWkMWXBAHJ7IlcUpg9wgN1mQF-slmGYPjMfHRtG8ggit")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set in .env")
    return genai.Client(api_key=api_key)