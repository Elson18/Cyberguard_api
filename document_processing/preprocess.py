import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from Chatbot.document_processing.downloadorg import extract_PDF_Text
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter

def sanitize_text(text):

    text = text.lower()

    text = re.sub(r'[^A-Za-z0-9.,!?;:\"()\-\s]', ' ', text)

    text = re.sub(r'\s+', ' ', text).strip()

    return text

def chunk_text(text):

    text=sanitize_text(text)
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size = 800, chunk_overlap=100)
    chunks = text_splitter.split_text(text)
    return chunks
