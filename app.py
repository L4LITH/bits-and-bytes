import os
import time
import streamlit as st
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODELS = ["gemini-3.8-flash"]  # add a second model name from AI Studio as a backup

def ask_gemini(prompt):
    for model in MODELS:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt
                )
                return response.text
            except Exception as e:
                print(f"{model} attempt {attempt + 1} failed: {e}")
                time.sleep(2 * (attempt + 1))  # wait 2s, 4s, 6s
    return None

st.title("My First AI App")
text = st.text_area("Type something")

if st.button("Ask Gemini"):
    with st.spinner("Thinking..."):
        answer = ask_gemini(text)
    if answer:
        st.write(answer)
    else:
        st.error("The AI is busy right now. Please try again in a moment.")