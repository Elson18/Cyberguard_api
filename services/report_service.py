from bson import ObjectId
from database.mongodb import db_wrapper
from utils.response import success_response, error_response
from utils.helpers import serialize_doc

class ReportService:
    @staticmethod
    def get_student_profile(student_user_id):
        """Fetches the student profile combined with class detail context."""
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        student = db.students.find_one({"userId": student_user_id})
        if not student:
            return error_response("Student profile not found.", 404)
            
        class_details = {}
        class_id = student.get("classId")
        if class_id:
            class_filter = {"_id": class_id}
            try:
                class_filter = {"_id": ObjectId(class_id)}
            except Exception:
                pass
            cls = db.classes.find_one(class_filter)
            if cls:
                class_details = {
                    "className": cls.get("className"),
                    "section": cls.get("section")
                }
                
        profile_data = {
            "studentId": student.get("studentId"),
            "userId": student.get("userId"),
            "name": student.get("name"),
            "rollNumber": student.get("rollNumber"),
            "classId": student.get("classId"),
            "class": class_details
        }
        
        return success_response(data=serialize_doc(profile_data))

    @staticmethod
    def get_student_marks(student_id, exam=None, academic_year=None, exam_id=None):
        """Fetches student marks, optionally filtered by exam, academic year, or examId."""
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        query = {"studentId": student_id}
        if exam:
            query["exam"] = exam
        if academic_year:
            query["academicYear"] = academic_year
        if exam_id:
            query["examId"] = exam_id
            
        marks = list(db.marks.find(query))
        return success_response(data=serialize_doc(marks))

    @staticmethod
    def get_student_report_card(student_id, exam=None, academic_year=None, exam_id=None):
        """Retrieves published report cards for the student."""
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        query = {"studentId": student_id}
        if exam:
            query["exam"] = exam
        if academic_year:
            query["academicYear"] = academic_year
        if exam_id:
            query["examId"] = exam_id
            
        reports = list(db.report_cards.find(query))
        return success_response(data=serialize_doc(reports))

    @staticmethod
    def get_student_rank(student_id, exam=None, academic_year=None, exam_id=None):
        """Retrieves student ranking information for published examinations."""
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        query = {"studentId": student_id}
        if exam:
            query["exam"] = exam
        if academic_year:
            query["academicYear"] = academic_year
        if exam_id:
            query["examId"] = exam_id
            
        reports = list(db.report_cards.find(query))
        
        ranks = []
        for rep in reports:
            ranks.append({
                "examId": rep.get("examId"),
                "exam": rep.get("exam"),
                "academicYear": rep.get("academicYear"),
                "rank": rep.get("rank"),
                "totalMarks": rep.get("totalMarks"),
                "percentage": rep.get("percentage"),
                "grade": rep.get("grade"),
                "passed": rep.get("passed")
            })
            
        return success_response(data=serialize_doc(ranks))

    @staticmethod
    def get_student_dashboard(student_user_id):
        """Compiles student dashboard data including profile, latest exam report, and summary statistics."""
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        student = db.students.find_one({"userId": student_user_id})
        if not student:
            return error_response("Student profile not found.", 404)
            
        student_id = student["studentId"]
        
        # Get all published report cards sorted by published timestamp descending
        report_cards = list(db.report_cards.find({"studentId": student_id}).sort("publishedAt", -1))
        
        latest_exam = {}
        if report_cards:
            latest_exam = report_cards[0]
            
        # Summary statistics
        total_exams = len(report_cards)
        passed_exams = sum(1 for r in report_cards if r.get("passed", False))
        
        avg_percentage = 0.0
        if total_exams > 0:
            avg_percentage = sum(r.get("percentage", 0.0) for r in report_cards) / total_exams
            avg_percentage = round(avg_percentage, 2)
            
        summary = {
            "totalExams": total_exams,
            "passedExams": passed_exams,
            "averagePercentage": avg_percentage,
            "passRate": round((passed_exams / total_exams * 100), 2) if total_exams > 0 else 0.0
        }
        
        dashboard_data = {
            "student": student,
            "latestExam": latest_exam,
            "summary": summary
        }
        
        return success_response(message="Dashboard data retrieved successfully.", data=serialize_doc(dashboard_data))

    @staticmethod
    def get_pdf_report_card(student_user_id, exam_id):
        """Retrieves details and generates the PDF bytes for the report card."""
        db = db_wrapper.db
        if db is None:
            return None, "Database connection not ready.", 500
            
        student = db.students.find_one({"userId": student_user_id})
        if not student:
            return None, "Student profile not found.", 404
            
        student_id = student["studentId"]
        
        report_card = db.report_cards.find_one({"studentId": student_id, "examId": exam_id})
        if not report_card:
            return None, "Report card not found or not published for this exam.", 404
            
        exam = db.exams.find_one({"examId": exam_id})
        if not exam:
            return None, "Exam details not found.", 404
            
        from services.pdf_service import PDFService
        pdf_bytes = PDFService.generate_report_card_pdf(student, exam, report_card)
        return pdf_bytes, None, 200
