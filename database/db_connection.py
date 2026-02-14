from pymongo import MongoClient
from config import Config
from database.logging_config import logger

config = Config()

def get_db():
    try:
        client = MongoClient(config.MONGO_DB_URL)
        db = client["CyberChatbot"]
        return db
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        return None

def get_next_sequence_value(sequence_name: str) -> int:
    db = get_db()
    if db is None:
        raise Exception("Database connection failed.")

    counter = db.counters.find_one_and_update(
        {'_id': sequence_name},
        {'$inc': {'sequence': 1}},
        upsert=True,
        return_document=True
    )
    return counter['sequence']

def generate_custom_patient_id() -> str:
    sequence = get_next_sequence_value("user_info")
    return f"USER-{sequence:06d}"

def generate_custom_Cyber_id() -> str:
    sequence = get_next_sequence_value("cyber_security")
    return f"CYBER-{sequence:06d}"
