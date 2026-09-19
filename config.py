import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/cyberguard_db")
    MONGO_DB_URL = os.getenv("MONGO_DB_URL", os.getenv("MONGO_URI", "mongodb://localhost:27017/cyberguard_db"))
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-jwt-key-change-this-in-production")
    PORT = int(os.getenv("PORT", 8765))
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    
    DEFAULT_ADMIN_USER_ID = os.getenv("DEFAULT_ADMIN_USER_ID", "admin")
    DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "Admin@123")

    # Vector store & LLM Configuration
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    PERSIST_DIRECTORY = os.getenv("PERSIST_DIRECTORY", os.path.join(BASE_DIR, "chroma_db"))
    COLLECTION_NAME = os.getenv("COLLECTION_NAME", "cyber_security_docs")
    
    # JWT Configuration
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
