from datetime import datetime, timezone
from bson import ObjectId
from database.mongodb import db_wrapper
from services.ranking_service import RankingService
from utils.response import success_response, error_response

class MarksService:
    @staticmethod
    def enter_marks(teacher_id, student_id, class_id, subject_id, exam, marks_value, academic_year):
        """
        Enters a marks record. Automatically recalculates rankings if already published.
        """
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        # 1. Verify teacher assignment
        teacher = db.teachers.find_one({"teacherId": teacher_id})
        if not teacher:
            return error_response("Teacher not found.", 404)
        if class_id not in teacher.get("assignedClasses", []):
            return error_response("You are not assigned to this class.", 403)
            
        # 2. Verify student exists and belongs to this class
        student = db.students.find_one({"studentId": student_id})
        if not student:
            return error_response("Student not found.", 404)
        if student.get("classId") != class_id:
            return error_response("Student does not belong to the specified class.", 400)
            
        # 3. Verify subject exists
        subject_filter = {"_id": subject_id}
        try:
            # Check if it's a valid ObjectId
            subject_filter = {"_id": ObjectId(subject_id)}
        except Exception:
            pass
            
        subject = db.subjects.find_one(subject_filter)
        if not subject:
            # Fallback lookup by subjectName
            subject = db.subjects.find_one({"subjectName": subject_id})
            if not subject:
                return error_response("Subject not found.", 404)
            subject_id = str(subject["_id"])
        else:
            subject_id = str(subject["_id"])
            
        # 4. Upsert marks record
        now = datetime.now(timezone.utc)
        filter_query = {
            "studentId": student_id,
            "classId": class_id,
            "subjectId": subject_id,
            "exam": exam,
            "academicYear": academic_year
        }
        
        update_data = {
            "teacherId": teacher_id,
            "marks": marks_value,
            "updatedAt": now
        }
        
        # Check if record exists to set createdAt
        existing = db.marks.find_one(filter_query)
        if not existing:
            update_data["createdAt"] = now
            
        db.marks.update_one(filter_query, {"$set": update_data}, upsert=True)
        
        # 5. If rankings for this class/exam/year are already published, update automatically
        if RankingService.is_published(class_id, exam, academic_year):
            RankingService.calculate_and_save_rankings(class_id, exam, academic_year)
            
        return success_response(message="Marks entered successfully.")

    @staticmethod
    def edit_marks(teacher_id, mark_id, new_marks_value):
        """
        Edits an existing marks record. Automatically recalculates rankings if already published.
        """
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        try:
            m_id = ObjectId(mark_id)
        except Exception:
            return error_response("Invalid mark ID format.", 400)
            
        mark = db.marks.find_one({"_id": m_id})
        if not mark:
            return error_response("Marks record not found.", 404)
            
        # Verify teacher authorization (must be the one who entered it, or assigned to the class)
        if mark.get("teacherId") != teacher_id:
            teacher = db.teachers.find_one({"teacherId": teacher_id})
            if not teacher or mark.get("classId") not in teacher.get("assignedClasses", []):
                return error_response("You are not authorized to modify these marks.", 403)
                
        now = datetime.now(timezone.utc)
        db.marks.update_one(
            {"_id": m_id},
            {"$set": {"marks": new_marks_value, "updatedAt": now}}
        )
        
        # Trigger automatic rank recalculation if published
        class_id = mark["classId"]
        exam = mark["exam"]
        academic_year = mark["academicYear"]
        
        if RankingService.is_published(class_id, exam, academic_year):
            RankingService.calculate_and_save_rankings(class_id, exam, academic_year)
            
        return success_response(message="Marks updated successfully.")

    @staticmethod
    def publish_marks(teacher_id, class_id, exam, academic_year):
        """
        Publishes marks and generates the report cards and rankings.
        """
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        # Verify teacher is assigned to the class
        teacher = db.teachers.find_one({"teacherId": teacher_id})
        if not teacher:
            return error_response("Teacher not found.", 404)
        if class_id not in teacher.get("assignedClasses", []):
            return error_response("You are not assigned to this class.", 403)
            
        # Verify marks have been entered for this configuration
        count = db.marks.count_documents({
            "classId": class_id,
            "exam": exam,
            "academicYear": academic_year
        })
        if count == 0:
            return error_response("No marks have been entered for this class, exam, and academic year.", 400)
            
        success = RankingService.calculate_and_save_rankings(class_id, exam, academic_year)
        if success:
            return success_response(message="Marks published and rankings computed successfully.")
        else:
            return error_response("Failed to publish marks. Ensure students exist in the class.", 500)
