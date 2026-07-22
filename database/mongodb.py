from pymongo import MongoClient
from config import Config

class Database:
    def __init__(self):
        self.client = None
        self.db = None

    def init_app(self, app):
        mongo_uri = app.config.get("MONGO_URI", Config.MONGO_URI)
        # Initialize MongoClient with reasonable timeout
        self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)

        # Extract db name from URI or use default
        db_name = mongo_uri.split('/')[-1] if '/' in mongo_uri else 'student_rank_card_db'
        if '?' in db_name:
            db_name = db_name.split('?')[0]
        if not db_name or db_name == 'localhost:27017' or db_name.startswith('localhost:'):
            db_name = 'student_rank_card_db'
            
        self.db = self.client[db_name]
        # Attach to app context for convenience
        app.db = self.db
        
        # Ensure Indexes
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
        
        # Teachers indexes
        self.db.teachers.create_index("teacherId", unique=True)
        self.db.teachers.create_index("userId", unique=True)
        
        # Students indexes
        self.db.students.create_index("studentId", unique=True)
        self.db.students.create_index("userId", unique=True)
        self.db.students.create_index([("classId", 1), ("rollNumber", 1)], unique=True)
        
        # Classes indexes
        self.db.classes.create_index([("className", 1), ("section", 1)], unique=True)
        
        # Subjects indexes
        self.db.subjects.create_index("subjectName", unique=True)
        
        # Marks indexes: unique constraint for a student, class, subject, exam, academic year
        self.db.marks.create_index([
            ("studentId", 1),
            ("classId", 1),
            ("subjectId", 1),
            ("exam", 1),
            ("academicYear", 1)
        ], unique=True)
        
        # Token Blocklist for blacklisting logged-out JWT tokens
        self.db.token_blocklist.create_index("jti", unique=True)
        self.db.token_blocklist.create_index("expiresAt", expireAfterSeconds=0)
        
        # Exams indexes
        self.db.exams.create_index("examId", unique=True)
        try:
            self.db.exams.create_index([("classId", 1), ("term", 1), ("academicYear", 1)], unique=True)
        except Exception as e:
            print(f"Warning: Could not build compound unique index for exams: {e}")
        
        # Audit logs index
        self.db.audit_logs.create_index("timestamp")
        
        # Report Cards / Rankings indexes
        self.db.report_cards.create_index([
            ("studentId", 1),
            ("classId", 1),
            ("exam", 1),
            ("academicYear", 1)
        ], unique=True)
        
        # Compound unique index for new examId based report cards
        self.db.report_cards.create_index([
            ("studentId", 1),
            ("classId", 1),
            ("examId", 1)
        ], unique=True, partialFilterExpression={"examId": {"$exists": True}})

        # Discussions indexes
        self.db.discussions.create_index("studentId")
        self.db.discussions.create_index("teacherId")
        self.db.discussions.create_index("discussionId", unique=True)
        self.db.discussions.create_index("status")
        self.db.discussions.create_index("createdAt")

        # Discussion messages indexes
        self.db.discussion_messages.create_index("discussionId")
        self.db.discussion_messages.create_index("createdAt")

        # Fee structures indexes
        self.db.fee_structures.create_index("feeStructureId", unique=True)
        self.db.fee_structures.create_index("status")
        self.db.fee_structures.create_index("dueDate")
        self.db.fee_structures.create_index("classIds")

        # Student fees indexes
        self.db.student_fees.create_index("studentId")
        self.db.student_fees.create_index("classId")
        self.db.student_fees.create_index("feeStructureId")
        self.db.student_fees.create_index("status")
        self.db.student_fees.create_index([("studentId", 1), ("feeStructureId", 1)], unique=True)

        # Fee payments indexes
        self.db.fee_payments.create_index("paymentId", unique=True)
        self.db.fee_payments.create_index("studentId")
        self.db.fee_payments.create_index("feeStructureId")
        self.db.fee_payments.create_index("transactionId", unique=True, sparse=True)

        # Fee notifications indexes
        self.db.fee_notifications.create_index("studentId")

        # Online Exam Questions indexes
        self.db.exam_questions.create_index("examId")
        self.db.exam_questions.create_index([("examId", 1), ("questionId", 1)], unique=True)

        # Online Exam Attempts indexes
        self.db.exam_attempts.create_index("attemptId", unique=True)
        self.db.exam_attempts.create_index([("examId", 1), ("studentId", 1)], unique=True)

        # Student Answers indexes
        self.db.student_answers.create_index([("attemptId", 1), ("questionId", 1)], unique=True)

        # Exam Results indexes
        self.db.exam_results.create_index([("examId", 1), ("studentId", 1)], unique=True)


# Global database wrapper instance
db_wrapper = Database()
