import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from vector_stores.chromadb_store import LocalChromaDb
from langchain_core.messages import HumanMessage, SystemMessage
from config import Config
import boto3
import json

config = Config()
chromadb_model_Azure = LocalChromaDb()

from groq import Groq
import time

# Initialize Groq client
client = Groq(api_key=config.GROQ_API_KEY)

def generate_response_groq(user_input, k=3, max_retries=3):
    # Retrieve context from ChromaDB
    try:
        user_chunk = chromadb_model_Azure.response_query(user_input, k=k)
        context = "\n".join(user_chunk)
    except Exception as exc:
        print(f"RAG retrieval error: {exc}")
        context = ""

    groq_api_key = config.GROQ_API_KEY or os.getenv("GROQ_API_KEY") or ""
    if not groq_api_key.strip():
        if context.strip():
            return f"### Knowledge Base Context\n\n{context}"
        return "CyberGuard Assistant is active. Please add your `GROQ_API_KEY` to the `.env` file for full AI LLM capabilities."

    prompt = f"""You are a helpful assistant.

Context:
{context}

Question:
{user_input}
"""

    for attempt in range(max_retries):
        try:
            client = Groq(api_key=groq_api_key.strip())
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1024
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(1)

    if context.strip():
        return f"### Knowledge Base Context\n\n{context}"
    return "Unable to generate AI response at this time. Please try again later."