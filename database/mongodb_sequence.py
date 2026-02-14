
from database.db_connection import get_db
from database.logging_config import logger 
 
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
   
def generate_custom_user_id() -> str:
    """Generate a custom patient ID in format PAT-XXXXXX"""
    sequence = get_next_sequence_value("user_info")
    return f"USER-{sequence:06d}"
 
def generate_custom_doctor_id() -> str:
    """Generate a custom doctor ID in format DOC-XXXXXX"""
    sequence = get_next_sequence_value("cyber_security")
    return f"DOC-{sequence:06d}"