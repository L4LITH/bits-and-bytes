import time
import os, json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

PROMPT = """You are reading a medical document (prescription or lab report).
Extract the information and return ONLY valid JSON in exactly this shape:

{
  "date": "YYYY-MM-DD or null",
  "doctor": "name or null",
  "doc_type": "prescription or lab_report or other",
  "diagnosis": "text or null",
  "medicines": [{"name": "", "generic": "", "dose": "", "frequency": ""}],,
  "labs": [{"test_name": "", "value": "", "unit": ""}]
}

Rules:
- Use null for anything not visible. Never guess or invent values.
- Dates must be YYYY-MM-DD.
- If there are no medicines or no labs, use an empty list.
- "generic" is the active ingredient in lowercase (for example Dolo 650 -> "paracetamol"). Use null if you are not confident.
"""

MODELS = ["gemini-3.8-flash","gemini-3.5-flash-lite","gemini-3.1-flash-lite"]  # add a backup model name from AI Studio if you want a fallback

def extract_record(image_bytes, mime_type="image/png"):
    last_error = None
    for model in MODELS:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=[
                        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                        PROMPT,
                    ],
                    config=types.GenerateContentConfig(response_mime_type="application/json"),
                )
                return json.loads(response.text)
            except Exception as e:
                last_error = e
                print(f"{model} attempt {attempt + 1} failed: {e}")
                time.sleep(2 * (attempt + 1))
    raise last_error

if __name__ == "__main__":
    with open("sample_rx.png", "rb") as f:
        data = extract_record(f.read())
    print(json.dumps(data, indent=2))