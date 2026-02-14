import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from vector_stores.chromadb_store import LocalChromaDb
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from config import Config
import boto3
import json

config = Config()
chromadb_model_Azure = LocalChromaDb()


from mistralai import Mistral

# Initialize configuration and ChromaDB

# Initialize Mistral client
client = Mistral(api_key=config.MISTRALAI_API_KEY)

import time

def generate_response_mistral(user_input, k=3, max_retries=5):
    user_chunk = chromadb_model_Azure.response_query(user_input, k=3)
    context = "\n".join(user_chunk)
    prompt = f"""You are a helpful assistant.
Context:
{context}
Question:
{user_input}"""

    for attempt in range(max_retries):
        try:
            response = client.chat.complete(
                model="mistral-small-latest",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            time.sleep(2 ** attempt)  # exponential backoff
    return "Unable to generate response at this time. Please try again later."

