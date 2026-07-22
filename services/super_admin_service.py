from datetime import datetime, timezone
from bson import ObjectId
from database.mongodb import db_wrapper
from utils.helpers import hash_password, serialize_doc
from utils.response import success_response, error_response

class SuperAdminService:
    @staticmethod
    def create_teacher(user_id, password, name, department, teacher_id=None):
        """Creates a teacher account (User collection + Teacher collection)."""
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        # Check user ID uniqueness
        if db.users.find_one({"userId": user_id}):
            return error_response("User ID already exists.", 400)
            
        t_id = teacher_id if teacher_id else user_id
        if db.teachers.find_one({"teacherId": t_id}):
            return error_response("Teacher ID already exists.", 400)
            
        now = datetime.now(timezone.utc)
        hashed = hash_password(password)
        
        # Create user record
        db.users.insert_one({
            "userId": user_id,
            "password": hashed,
            "role": "TEACHER",
            "active": True,
            "createdAt": now
        })
        
        # Create teacher record
        teacher_doc = {
            "teacherId": t_id,
            "userId": user_id,
            "name": name,
            "department": department,
            "assignedClasses": []
        }
        db.teachers.insert_one(teacher_doc)
        
        return success_response(
            message="Teacher account created successfully.",
            data=serialize_doc(teacher_doc),
            status_code=201
        )

    @staticmethod
    def create_student(user_id, password, name, class_id, roll_number, student_id=None):
        """Creates a student account (User collection + Student collection)."""
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        # Check user ID uniqueness
        if db.users.find_one({"userId": user_id}):
            return error_response("User ID already exists.", 400)
            
        s_id = student_id if student_id else user_id
        if db.students.find_one({"studentId": s_id}):
            return error_response("Student ID already exists.", 400)
            
        # Verify class exists
        class_filter = {"_id": class_id}
        if ObjectId.is_valid(str(class_id)):
            try:
                class_filter = {"$or": [{"_id": class_id}, {"_id": ObjectId(class_id)}]}
            except Exception:
                pass
        cls = db.classes.find_one(class_filter)
        if not cls:
            return error_response("Class ID not found.", 404)
            
        # Verify roll number uniqueness in this class
        if db.students.find_one({"classId": class_id, "rollNumber": roll_number}):
            return error_response(f"Roll number '{roll_number}' already exists in this class.", 400)
            
        now = datetime.now(timezone.utc)
        hashed = hash_password(password)
        
        # Create user record
        db.users.insert_one({
            "userId": user_id,
            "password": hashed,
            "role": "STUDENT",
            "active": True,
            "createdAt": now
        })
        
        # Create student record
        student_doc = {
            "studentId": s_id,
            "userId": user_id,
            "name": name,
            "classId": class_id,
            "rollNumber": roll_number
        }
        db.students.insert_one(student_doc)
        
        return success_response(
            message="Student account created successfully.",
            data=serialize_doc(student_doc),
            status_code=201
        )

    @staticmethod
    def get_teachers():
        """Returns all teachers."""
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
        teachers = list(db.teachers.find({}))
        return success_response(data=serialize_doc(teachers))

    @staticmethod
    def get_students():
        """Returns all students."""
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
        students = list(db.students.find({}))
        return success_response(data=serialize_doc(students))

    @staticmethod
    def create_class(class_name, section, class_teacher=None):
        """Creates a class record and assigns it to classTeacher if provided."""
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        # Ensure class section uniqueness
        if db.classes.find_one({"className": class_name, "section": section}):
            return error_response(f"Class '{class_name}' section '{section}' already exists.", 400)
            
        # Validate teacher if assigned
        if class_teacher:
            teacher = db.teachers.find_one({"teacherId": class_teacher})
            if not teacher:
                return error_response("Class teacher ID not found.", 404)
                
        class_doc = {
            "className": class_name,
            "section": section,
            "classTeacher": class_teacher
        }
        
        result = db.classes.insert_one(class_doc)
        class_doc["_id"] = str(result.inserted_id)
        
        # Update teacher assignedClasses to include this class ID
        if class_teacher:
            db.teachers.update_one(
                {"teacherId": class_teacher},
                {"$addToSet": {"assignedClasses": class_doc["_id"]}}
            )
            
        return success_response(
            message="Class created successfully.",
            data=serialize_doc(class_doc),
            status_code=201
        )

    @staticmethod
    def create_subject(subject_name):
        """Creates a subject record."""
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        if db.subjects.find_one({"subjectName": subject_name}):
            return error_response(f"Subject '{subject_name}' already exists.", 400)
            
        subject_doc = {
            "subjectName": subject_name
        }
        
        result = db.subjects.insert_one(subject_doc)
        subject_doc["_id"] = str(result.inserted_id)
        
        return success_response(
            message="Subject created successfully.",
            data=serialize_doc(subject_doc),
            status_code=201
        )

    @staticmethod
    def assign_teacher(teacher_id, class_id):
        """Assigns a teacher to a class."""
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        teacher = db.teachers.find_one({"teacherId": teacher_id})
        if not teacher:
            return error_response("Teacher not found.", 404)
            
        class_filter = {"_id": class_id}
        if ObjectId.is_valid(str(class_id)):
            try:
                class_filter = {"$or": [{"_id": class_id}, {"_id": ObjectId(class_id)}]}
            except Exception:
                pass
        cls = db.classes.find_one(class_filter)
        if not cls:
            return error_response("Class not found.", 404)
            
        # Add class ID to teacher's assignments
        db.teachers.update_one(
            {"teacherId": teacher_id},
            {"$addToSet": {"assignedClasses": class_id}}
        )
        
        # Set classTeacher field in class document
        db.classes.update_one(
            class_filter,
            {"$set": {"classTeacher": teacher_id}}
        )
        
        return success_response(message=f"Teacher '{teacher_id}' successfully assigned to class '{class_id}'.")
