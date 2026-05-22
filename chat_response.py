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

def generate_response_groq(user_input, k=3, max_retries=5):

    # Retrieve context from ChromaDB
    user_chunk = chromadb_model_Azure.response_query(user_input, k=k)
    context = "\n".join(user_chunk)

    prompt = f"""You are a helpful assistant.

Context:
{context}

Question:
{user_input}
"""

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",   # You can also use mixtral-8x7b-32768
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1024
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(2 ** attempt)  # exponential backoff

    return "Unable to generate response at this time. Please try again later."