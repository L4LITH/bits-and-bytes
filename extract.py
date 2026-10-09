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
  "medicines": [{"name": "", "dose": "", "frequency": ""}],
  "labs": [{"test_name": "", "value": "", "unit": ""}]
}

Rules:
- Use null for anything not visible. Never guess or invent values.
- Dates must be YYYY-MM-DD.
- If there are no medicines or no labs, use an empty list.
"""

def extract_record(image_bytes, mime_type="image/png"):
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            PROMPT,
        ],
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    return json.loads(response.text)

if __name__ == "__main__":
    with open("sample_rx.png", "rb") as f:
        data = extract_record(f.read())
    print(json.dumps(data, indent=2))