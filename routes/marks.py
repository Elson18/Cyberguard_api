from flask import Blueprint, request
from pydantic import ValidationError
from middleware.role_required import role_required
from services.marks_service import MarksService
from models.marks_model import CreateMarksSchema, UpdateMarksSchema, PublishMarksSchema
from utils.response import error_response
from flask_jwt_extended import get_jwt_identity
from database.mongodb import db_wrapper

marks_bp = Blueprint("marks", __name__, url_prefix="/api")

def get_teacher_id_from_identity(user_id):
    db = db_wrapper.db
    if db is None:
        return None
    teacher = db.teachers.find_one({"userId": user_id})
    return teacher.get("teacherId") if teacher else None

@marks_bp.route("/marks", methods=["POST"])
@role_required("TEACHER")
def enter_marks():
    """Endpoint for teachers to enter student marks."""
    current_user_id = get_jwt_identity()
    teacher_id = get_teacher_id_from_identity(current_user_id)
    if not teacher_id:
        return error_response("Teacher profile not found.", 404)
        
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is missing.", 400)
        validated = CreateMarksSchema(**data)
    except ValidationError as err:
        return error_response(f"Validation error: {err.errors()[0]['msg']}", 400)
    except Exception:
        return error_response("Invalid JSON format in body.", 400)
        
    return MarksService.enter_marks(
        teacher_id=teacher_id,
        student_id=validated.studentId,
        class_id=validated.classId,
        subject_id=validated.subjectId,
        exam=validated.exam,
        marks_value=validated.marks,
        academic_year=validated.academicYear
    )

@marks_bp.route("/marks/<markId>", methods=["PUT"])
@role_required("TEACHER")
def edit_marks(markId):
    """Endpoint for teachers to edit student marks."""
    current_user_id = get_jwt_identity()
    teacher_id = get_teacher_id_from_identity(current_user_id)
    if not teacher_id:
        return error_response("Teacher profile not found.", 404)
        
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is missing.", 400)
        validated = UpdateMarksSchema(**data)
    except ValidationError as err:
        return error_response(f"Validation error: {err.errors()[0]['msg']}", 400)
    except Exception:
        return error_response("Invalid JSON format in body.", 400)
        
    return MarksService.edit_marks(
        teacher_id=teacher_id,
        mark_id=markId,
        new_marks_value=validated.marks
    )

@marks_bp.route("/marks/publish", methods=["POST"])
@role_required("TEACHER")
def publish_marks():
    """Endpoint for teachers to calculate ranking and publish report cards."""
    current_user_id = get_jwt_identity()
    teacher_id = get_teacher_id_from_identity(current_user_id)
    if not teacher_id:
        return error_response("Teacher profile not found.", 404)
        
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is missing.", 400)
        validated = PublishMarksSchema(**data)
    except ValidationError as err:
        return error_response(f"Validation error: {err.errors()[0]['msg']}", 400)
    except Exception:
        return error_response("Invalid JSON format in body.", 400)
        
    return MarksService.publish_marks(
        teacher_id=teacher_id,
        class_id=validated.classId,
        exam=validated.exam,
        academic_year=validated.academicYear
    )
