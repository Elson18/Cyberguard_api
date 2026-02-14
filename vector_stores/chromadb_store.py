import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from config import Config
from document_processing.preprocess import chunk_text
from langchain_core.documents import Document

config = Config()

class LocalChromaDb:
    def __init__(self):
        self.embed_model = None
        self.vectorstore = None

    def init_vectortore(self):
        if self.vectorstore is None:
            # Load HuggingFace embedding model (local, no API key required)
            self.embed_model = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )

            self.vectorstore = Chroma(
                collection_name=config.COLLECTION_NAME,
                persist_directory=config.PERSIST_DIRECTORY_CHROMADB,
                embedding_function=self.embed_model
            )

    def store_the_chunk(self, text):
        self.init_vectortore()

        chunks = chunk_text(text)
        docs = [Document(page_content=chunk) for chunk in chunks]

        self.vectorstore.add_documents(docs)
        return "Documents stored in ChromaDB"

    def response_query(self, user_query, k=3):
        self.init_vectortore()
        results = self.vectorstore.similarity_search(user_query, k=k)
        return [doc.page_content for doc in results]