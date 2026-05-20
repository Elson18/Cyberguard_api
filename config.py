from dotenv import load_dotenv
import os 

load_dotenv()

class Config:
    def __init__(self):
        self.FILE_PATH = os.getenv("FILE_PATH")

        #Sql Collection
        self.COLLECTION_NAME = os.getenv("COLLECTION_NAME")
        self.PERSIST_DIRECTORY = os.getenv("PERSIST_DIRECTORY")

        # self.select_model = {}

        self.GROQ_API_KEY = os.getenv("GROQ_API_KEY")

        self.MONGO_DB_URL = os.getenv("MONGO_DB_URL")