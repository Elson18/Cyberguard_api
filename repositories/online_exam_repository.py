from database.mongodb import db_wrapper
from bson import ObjectId

class OnlineExamRepository:
    @staticmethod
    def get_db():
        return db_wrapper.db

    @classmethod
    def get_exam_by_id(cls, exam_id):
        db = cls.get_db()
        return db.exams.find_one({"examId": exam_id, "isOnline": True})

    @classmethod
    def find_exams(cls, query):
        db = cls.get_db()
        query["isOnline"] = True
        return list(db.exams.find(query))

    @classmethod
    def create_exam(cls, exam_doc):
        db = cls.get_db()
        exam_doc["isOnline"] = True
        # Set compatibility fields for offline exam index
        exam_doc["classId"] = f"ONLINE_{exam_doc['examId']}"
        exam_doc["term"] = "ONLINE"
        db.exams.insert_one(exam_doc)
        return exam_doc

    @classmethod
    def update_exam(cls, exam_id, update_fields):
        db = cls.get_db()
        db.exams.update_one({"examId": exam_id, "isOnline": True}, {"$set": update_fields})
        return cls.get_exam_by_id(exam_id)

    @classmethod
    def delete_exam(cls, exam_id):
        db = cls.get_db()
        db.exams.delete_one({"examId": exam_id, "isOnline": True})
        db.exam_questions.delete_many({"examId": exam_id})

    @classmethod
    def get_questions_by_exam_id(cls, exam_id):
        db = cls.get_db()
        return list(db.exam_questions.find({"examId": exam_id}).sort("order", 1))

    @classmethod
    def bulk_create_questions(cls, question_docs):
        db = cls.get_db()
        if question_docs:
            db.exam_questions.insert_many(question_docs)

    @classmethod
    def delete_questions_by_exam_id(cls, exam_id):
        db = cls.get_db()
        db.exam_questions.delete_many({"examId": exam_id})

    @classmethod
    def get_attempt_by_student_and_exam(cls, student_id, exam_id):
        db = cls.get_db()
        return db.exam_attempts.find_one({"studentId": student_id, "examId": exam_id})

    @classmethod
    def get_attempt_by_id(cls, attempt_id):
        db = cls.get_db()
        return db.exam_attempts.find_one({"attemptId": attempt_id})

    @classmethod
    def create_attempt(cls, attempt_doc):
        db = cls.get_db()
        db.exam_attempts.insert_one(attempt_doc)
        return attempt_doc

    @classmethod
    def update_attempt(cls, attempt_id, update_fields):
        db = cls.get_db()
        db.exam_attempts.update_one({"attemptId": attempt_id}, {"$set": update_fields})
        return cls.get_attempt_by_id(attempt_id)

    @classmethod
    def get_attempts_by_exam_id(cls, exam_id):
        db = cls.get_db()
        return list(db.exam_attempts.find({"examId": exam_id}))

    @classmethod
    def count_attempts_by_status(cls, exam_id, status):
        db = cls.get_db()
        return db.exam_attempts.count_documents({"examId": exam_id, "status": status})

    @classmethod
    def get_student_answer(cls, attempt_id, question_id):
        db = cls.get_db()
        return db.student_answers.find_one({"attemptId": attempt_id, "questionId": question_id})

    @classmethod
    def save_student_answer(cls, answer_doc):
        db = cls.get_db()
        db.student_answers.update_one(
            {"attemptId": answer_doc["attemptId"], "questionId": answer_doc["questionId"]},
            {"$set": answer_doc},
            upsert=True
        )
        return answer_doc

    @classmethod
    def get_answers_by_attempt(cls, attempt_id):
        db = cls.get_db()
        return list(db.student_answers.find({"attemptId": attempt_id}))

    @classmethod
    def get_result(cls, exam_id, student_id):
        db = cls.get_db()
        return db.exam_results.find_one({"examId": exam_id, "studentId": student_id})

    @classmethod
    def save_result(cls, result_doc):
        db = cls.get_db()
        db.exam_results.update_one(
            {"examId": result_doc["examId"], "studentId": result_doc["studentId"]},
            {"$set": result_doc},
            upsert=True
        )
        return result_doc

    @classmethod
    def publish_results(cls, exam_id):
        db = cls.get_db()
        db.exam_results.update_many({"examId": exam_id}, {"$set": {"published": True}})

    @classmethod
    def get_student_by_userId(cls, user_id):
        db = cls.get_db()
        return db.students.find_one({"userId": user_id})

    @classmethod
    def get_student_by_studentId(cls, student_id):
        db = cls.get_db()
        return db.students.find_one({"studentId": student_id})

    @classmethod
    def get_students_by_classIds(cls, class_ids):
        db = cls.get_db()
        return list(db.students.find({"classId": {"$in": class_ids}}))

    @classmethod
    def get_teacher_by_userId(cls, user_id):
        db = cls.get_db()
        return db.teachers.find_one({"userId": user_id})

    @classmethod
    def create_notification(cls, notification_doc):
        db = cls.get_db()
        db.notifications.insert_one(notification_doc)

    @classmethod
    def get_class_by_id(cls, class_id):
        db = cls.get_db()
        class_filter = {"_id": class_id}
        if ObjectId.is_valid(str(class_id)):
            try:
                class_filter = {"$or": [{"_id": class_id}, {"_id": ObjectId(class_id)}]}
            except Exception:
                pass
        return db.classes.find_one(class_filter)
        
    @classmethod
    def get_subject_by_id(cls, subject_id):
        db = cls.get_db()
        sub_filter = {"_id": subject_id}
        if ObjectId.is_valid(str(subject_id)):
            try:
                sub_filter = {"$or": [{"_id": subject_id}, {"_id": ObjectId(subject_id)}]}
            except Exception:
                pass
        subject = db.subjects.find_one(sub_filter)
        if not subject:
            subject = db.subjects.find_one({"subjectName": subject_id})
        return subject
