import sys
import os
from pymongo import MongoClient
import uuid
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from database.db_connection import *

config = Config()


class MongoDb:
    def __init__(self):
        try:
            self.mongo_client = MongoClient(config.MONGO_DB_URL)
            self.database = self.mongo_client["CyberChatbot"]
            self.cyber_security_info = self.database["cyber_security"]
            self.user_info = self.database["user_info"]
            self.case_info = self.database["case_info"]
            print("✅ MongoDB connected successfully.")
        except Exception as e:
            print("❌ MongoDB connection failed:", e)


    def cyber_security_info_table(self):
        return self.cyber_security_info

    def case_table(self):
        return self.case_info

    def user_info_table(self):
        return self.user_info 
    
    def add_new_user(self, name, phone_no, email, password,re_password):

        try:
        #     # Avoid duplicates (check both phone and email)
        #     existing = self.patfind_one({"email": email})

        #     if existing:
        #         print(" User already exists, skipping insert.")
        #   # Generate custom patient ID
            user_id = generate_custom_patient_id()

            user_doc = {
                "user_id": user_id,  # Ensure patient ID is stored
                "name": name,
                "phone_no": phone_no,
                "email": email,
                "password": password,
                "confrim_password": re_password,
                "PIN": str(uuid.uuid4()),
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }

            result = self.user_info.insert_one(user_doc)
            print(f"New user inserted with patient_id: {user_id}")
            return user_doc  # <-- Return the inserted document

        except Exception as e:
            print("Error adding new user:", e)
            return None
        

    def add_cyber_info(self, dept_name, dept_phone_no, dept_email,state):

        try:
            # Avoid duplicates (check both phone and email)
        #     existing = self.cyber_security_info_table.find_one({"email": dept_email})

        #     if existing:
        #         print(" User already exists, skipping insert.")
        #   # Generate custom patient ID
            user_id = generate_custom_Cyber_id()

            user_doc = {
                "user_id": user_id,  # Ensure patient ID is stored
                "Dept_name": dept_name,
                "phone_no": dept_phone_no,
                "email": dept_email,
                "State": state,
                "PIN": str(uuid.uuid4()),
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }

            result = self.cyber_security_info.insert_one(user_doc)
            print(f"New user inserted with patient_id: {user_id}")
            return user_doc  # <-- Return the inserted document

        except Exception as e:
            print("Error adding new user:", e)
            return None
    
    def find_the_user(self, phone_or_email):
        """Find patient by phone or email."""
        try:
            patient_filter = {"$or": [{"phone_no": phone_or_email}, {"email": phone_or_email}]}
            user = self.user_info.find_one(patient_filter)
            return user
        except Exception as e:
            print("Error finding user:", e)
            return None
        

    def add_case(self, name, phone, email, department):
        try:
            case_record = {
                "department": department,
                "user_name": name,
                "user_phone_number": phone,
                "user_email": email,
                "status": "booked",
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }

            result = self.case_info.insert_one(case_record)

            print("Case filed successfully. Case ID:", result.inserted_id)

        except Exception as e:
            print("Error filing case:", e)
    def find_user_by_id(self, user_id):
        return self.users.find_one({"user_id": user_id})


if __name__ == "__main__":
    print("Hello")
    mongo = MongoDb()
    d = mongo.add_cyber_info(dept_name="Tamil Nadu Cyber Crime Department",
    dept_phone_no="+91 9791656265",
    dept_email="gurubalan1707@gmail.com",
    state="Tamil Nadu"
)