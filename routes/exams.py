from flask import Blueprint, request
from pydantic import ValidationError
from flask_jwt_extended import get_jwt_identity, get_jwt
from middleware.role_required import role_required
from services.exam_service import ExamService
from models.exam_model import CreateExamSchema, UpdateExamSchema, BulkMarkEntrySchema, UpdateStudentMarksSchema
from utils.response import error_response
from database.mongodb import db_wrapper

exams_bp = Blueprint("exams", __name__, url_prefix="/api")

def get_teacher_id_from_identity(user_id):
    db = db_wrapper.db
    if db is None:
        return None
    teacher = db.teachers.find_one({"userId": user_id})
    return teacher.get("teacherId") if teacher else None

@exams_bp.route("/exams", methods=["POST"])
@role_required("SUPER_ADMIN", "TEACHER")
def create_exam():
    """Create a new exam (teacher or admin)."""
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get("role")
    
    if role == "SUPER_ADMIN":
        teacher_id = "admin"
    else:
        teacher_id = get_teacher_id_from_identity(current_user_id)
        if not teacher_id:
            return error_response("Teacher profile not found.", 404)
            
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is missing.", 400)
        validated = CreateExamSchema(**data)
    except ValidationError as err:
        return error_response(f"Validation error: {err.errors()[0]['msg']}", 400)
    except Exception:
        return error_response("Invalid JSON format in body.", 400)
        
    return ExamService.create_exam(teacher_id, validated.model_dump(), role=role)

@exams_bp.route("/exams", methods=["GET"])
@role_required("SUPER_ADMIN", "TEACHER")
def get_exams():
    """List all exams owned by the teacher (or all exams if admin) with support for query filters."""
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get("role")
    is_admin = (role == "SUPER_ADMIN")
    
    if is_admin:
        teacher_id = "admin"
    else:
        teacher_id = get_teacher_id_from_identity(current_user_id)
        if not teacher_id:
            return error_response("Teacher profile not found.", 404)
            
    filters = {
        "academicYear": request.args.get("academicYear"),
        "classId": request.args.get("classId"),
        "status": request.args.get("status")
    }
            
    return ExamService.get_exams(teacher_id, is_admin, filters)

@exams_bp.route("/exams/<examId>", methods=["GET"])
@role_required("SUPER_ADMIN", "TEACHER")
def get_exam(examId):
    """Retrieve details for a single exam."""
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get("role")
    is_admin = (role == "SUPER_ADMIN")
    
    if is_admin:
        teacher_id = "admin"
    else:
        teacher_id = get_teacher_id_from_identity(current_user_id)
        if not teacher_id:
            return error_response("Teacher profile not found.", 404)
            
    return ExamService.get_exam(teacher_id, is_admin, examId)

@exams_bp.route("/exams/<examId>", methods=["PUT"])
@role_required("SUPER_ADMIN", "TEACHER")
def update_exam(examId):
    """Update properties of an exam (only in DRAFT status)."""
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get("role")
    is_admin = (role == "SUPER_ADMIN")
    
    if is_admin:
        teacher_id = "admin"
    else:
        teacher_id = get_teacher_id_from_identity(current_user_id)
        if not teacher_id:
            return error_response("Teacher profile not found.", 404)
            
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is missing.", 400)
        validated = UpdateExamSchema(**data)
    except ValidationError as err:
        return error_response(f"Validation error: {err.errors()[0]['msg']}", 400)
    except Exception:
        return error_response("Invalid JSON format in body.", 400)
        
    return ExamService.update_exam(teacher_id, is_admin, examId, validated.model_dump(exclude_unset=True), role=role)

@exams_bp.route("/exams/<examId>", methods=["DELETE"])
@role_required("SUPER_ADMIN", "TEACHER")
def delete_exam(examId):
    """Delete an exam. Allowed for super admin or creators when in DRAFT and without marks entered."""
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get("role")
    is_admin = (role == "SUPER_ADMIN")
    
    if is_admin:
        teacher_id = "admin"
    else:
        teacher_id = get_teacher_id_from_identity(current_user_id)
        if not teacher_id:
            return error_response("Teacher profile not found.", 404)
            
    return ExamService.delete_exam(teacher_id, is_admin, examId, role=role)

@exams_bp.route("/exams/<examId>/marks/bulk", methods=["POST"])
@role_required("SUPER_ADMIN", "TEACHER")
def bulk_save_marks(examId):
    """Bulk enters marks for multiple students and subjects."""
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get("role")
    
    if role == "SUPER_ADMIN":
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
        exam = db.exams.find_one({"examId": examId})
        if not exam:
            return error_response("Exam not found.", 404)
        teacher_id = exam.get("createdBy")
    else:
        teacher_id = get_teacher_id_from_identity(current_user_id)
        if not teacher_id:
            return error_response("Teacher profile not found.", 404)
            
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is missing.", 400)
        validated = BulkMarkEntrySchema(**data)
    except ValidationError as err:
        return error_response(f"Validation error: {err.errors()[0]['msg']}", 400)
    except Exception:
        return error_response("Invalid JSON format in body.", 400)
        
    return ExamService.bulk_save_marks(
        teacher_id=teacher_id,
        exam_id=examId,
        students_marks=[s.model_dump() for s in validated.students],
        role=role
    )

@exams_bp.route("/exams/<examId>/students/<studentId>", methods=["PUT"])
@role_required("SUPER_ADMIN", "TEACHER")
def update_student_marks(examId, studentId):
    """Updates all subject marks for a single student."""
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get("role")
    is_admin = (role == "SUPER_ADMIN")
    
    if is_admin:
        teacher_id = "admin"
    else:
        teacher_id = get_teacher_id_from_identity(current_user_id)
        if not teacher_id:
            return error_response("Teacher profile not found.", 404)
            
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is missing.", 400)
        validated = UpdateStudentMarksSchema(**data)
    except ValidationError as err:
        return error_response(f"Validation error: {err.errors()[0]['msg']}", 400)
    except Exception:
        return error_response("Invalid JSON format in body.", 400)
        
    return ExamService.update_student_marks(
        teacher_id=teacher_id,
        is_admin=is_admin,
        exam_id=examId,
        student_id=studentId,
        subjects_marks=[s.model_dump() for s in validated.subjects],
        role=role
    )

@exams_bp.route("/exams/<examId>/marksheet", methods=["GET"])
@role_required("SUPER_ADMIN", "TEACHER")
def get_marksheet(examId):
    """Retrieves class details, subjects, students and existing marks for marksheet spreadsheet."""
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get("role")
    
    if role == "SUPER_ADMIN":
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
        exam = db.exams.find_one({"examId": examId})
        if not exam:
            return error_response("Exam not found.", 404)
        teacher_id = exam.get("createdBy")
    else:
        teacher_id = get_teacher_id_from_identity(current_user_id)
        if not teacher_id:
            return error_response("Teacher profile not found.", 404)
            
    return ExamService.get_marksheet(teacher_id, examId)

@exams_bp.route("/exams/<examId>/publish", methods=["POST"])
@role_required("SUPER_ADMIN", "TEACHER")
def publish_exam(examId):
    """Publish marks, calculate rankings and save report cards, and lock exam."""
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get("role")
    
    if role == "SUPER_ADMIN":
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
        exam = db.exams.find_one({"examId": examId})
        if not exam:
            return error_response("Exam not found.", 404)
        teacher_id = exam.get("createdBy")
    else:
        teacher_id = get_teacher_id_from_identity(current_user_id)
        if not teacher_id:
            return error_response("Teacher profile not found.", 404)
            
    return ExamService.publish_exam(teacher_id, examId, role=role)

@exams_bp.route("/exams/<examId>/unlock", methods=["POST"])
@role_required("SUPER_ADMIN")
def unlock_exam(examId):
    """Unlocks a published/locked exam back to DRAFT (Super Admin only)."""
    current_user_id = get_jwt_identity()
    return ExamService.unlock_exam(examId, current_user_id)

@exams_bp.route("/exams/<examId>/statistics", methods=["GET"])
@role_required("SUPER_ADMIN", "TEACHER")
def get_statistics(examId):
    """Get exam statistics metrics including top 10 students list."""
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get("role")
    is_admin = (role == "SUPER_ADMIN")
    
    if is_admin:
        teacher_id = "admin"
    else:
        teacher_id = get_teacher_id_from_identity(current_user_id)
        if not teacher_id:
            return error_response("Teacher profile not found.", 404)
            
    return ExamService.get_statistics(teacher_id, is_admin, examId)
