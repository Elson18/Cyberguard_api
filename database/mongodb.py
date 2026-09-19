import uuid
from pymongo import MongoClient
from config import Config

class MongoDb:
    def __init__(self):
        mongo_uri = getattr(Config, "MONGO_URI", "mongodb://localhost:27017/cyberguard_db")
        try:
            self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
            db_name = mongo_uri.split('/')[-1].split('?')[0] if '/' in mongo_uri else 'cyberguard_db'
            if not db_name or 'localhost' in db_name or db_name == 'student_rank_card_db':
                db_name = 'cyberguard_db'
            self.db = self.client[db_name]
        except Exception as e:
            print(f"Warning: Could not connect to MongoDB: {e}")
            self.client = None
            self.db = None

    def find_the_user(self, identifier: str):
        if self.db is None:
            return None
        try:
            user = self.db.users.find_one({
                "$or": [
                    {"email": identifier},
                    {"userId": identifier},
                    {"user_id": identifier},
                    {"name": identifier}
                ]
            })
            if user:
                if "user_id" not in user and "userId" in user:
                    user["user_id"] = user["userId"]
            return user
        except Exception as e:
            print(f"Error finding user: {e}")
            return None

    def add_new_user(self, name, phone_no, email, password, re_password):
        user_id = f"USER-{str(uuid.uuid4())[:8].upper()}"
        user_doc = {
            "user_id": user_id,
            "userId": user_id,
            "name": name,
            "email": email,
            "phone_no": phone_no,
            "password": password,
            "role": "USER",
            "active": True
        }
        if self.db is not None:
            try:
                self.db.users.insert_one(user_doc)
            except Exception as e:
                print(f"Error inserting user: {e}")
        return {"user_id": user_id}

    def add_case(self, fullname, phone, email, department="Cybercrime"):
        case_id = f"CASE-{str(uuid.uuid4())[:8].upper()}"
        case_doc = {
            "case_id": case_id,
            "fullname": fullname,
            "phone": phone,
            "email": email,
            "department": department
        }
        if self.db is not None:
            try:
                self.db.cases.insert_one(case_doc)
            except Exception as e:
                print(f"Error inserting case: {e}")
        return {"case_id": case_id}


class Database:
    def __init__(self):
        self.client = None
        self.db = None

    def init_app(self, app):
        mongo_uri = app.config.get("MONGO_URI", Config.MONGO_URI)
        self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)

        db_name = mongo_uri.split('/')[-1] if '/' in mongo_uri else 'cyberguard_db'
        if '?' in db_name:
            db_name = db_name.split('?')[0]
        if not db_name or 'localhost:' in db_name or db_name == 'student_rank_card_db':
            db_name = 'cyberguard_db'
            
        self.db = self.client[db_name]
        app.db = self.db
        
        try:
            self._ensure_indexes()
        except Exception as e:
            print(f"Warning: Could not initialize database indexes: {e}")
        return self.db

    def _ensure_indexes(self):
        if self.db is None:
            return
            
        # Users indexes
        self.db.users.create_index("userId", unique=True)
        self.db.users.create_index("email", unique=True, sparse=True)
        
        # Incident cases indexes
        self.db.cases.create_index("case_id", unique=True)
        self.db.cases.create_index("email")
        
        # Token Blocklist
        self.db.token_blocklist.create_index("jti", unique=True)
        self.db.token_blocklist.create_index("expiresAt", expireAfterSeconds=0)
        
        # Audit logs index
        self.db.audit_logs.create_index("timestamp")


db_wrapper = Database()
