from flask import Blueprint, request
from pydantic import ValidationError, BaseModel, Field
from middleware.role_required import role_required
from services.super_admin_service import SuperAdminService
from services.auth_service import AuthService
from models.teacher_model import CreateTeacherSchema
from models.student_model import CreateStudentSchema
from models.class_model import CreateClassSchema
from models.subject_model import CreateSubjectSchema
from models.user_model import ResetPasswordSchema
from utils.response import error_response

admin_bp = Blueprint("super_admin", __name__, url_prefix="/api/admin")

# Sub-schemas for route validation
class AssignTeacherSchema(BaseModel):
    teacherId: str = Field(..., description="Unique teacher ID to assign.")
    classId: str = Field(..., description="Class ID to assign the teacher to.")

class UserStatusSchema(BaseModel):
    active: bool = Field(..., description="Account activation state.")

@admin_bp.route("/create-teacher", methods=["POST"])
@role_required("SUPER_ADMIN")
def create_teacher():
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is missing.", 400)
        validated = CreateTeacherSchema(**data)
    except ValidationError as err:
        return error_response(f"Validation error: {err.errors()[0]['msg']}", 400)
    except Exception:
        return error_response("Invalid JSON format in body.", 400)
        
    return SuperAdminService.create_teacher(
        user_id=validated.userId,
        password=validated.password,
        name=validated.name,
        department=validated.department,
        teacher_id=validated.teacherId
    )

@admin_bp.route("/create-student", methods=["POST"])
@role_required("SUPER_ADMIN")
def create_student():
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is missing.", 400)
        validated = CreateStudentSchema(**data)
    except ValidationError as err:
        return error_response(f"Validation error: {err.errors()[0]['msg']}", 400)
    except Exception:
        return error_response("Invalid JSON format in body.", 400)
        
    return SuperAdminService.create_student(
        user_id=validated.userId,
        password=validated.password,
        name=validated.name,
        class_id=validated.classId,
        roll_number=validated.rollNumber,
        student_id=validated.studentId
    )

@admin_bp.route("/teachers", methods=["GET"])
@role_required("SUPER_ADMIN")
def get_teachers():
    return SuperAdminService.get_teachers()

@admin_bp.route("/students", methods=["GET"])
@role_required("SUPER_ADMIN")
def get_students():
    return SuperAdminService.get_students()

@admin_bp.route("/reset-password/<userId>", methods=["PUT"])
@role_required("SUPER_ADMIN")
def reset_password(userId):
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is missing.", 400)
        validated = ResetPasswordSchema(**data)
    except ValidationError as err:
        return error_response(f"Validation error: {err.errors()[0]['msg']}", 400)
    except Exception:
        return error_response("Invalid JSON format in body.", 400)
        
    return AuthService.reset_password(userId, validated.newPassword)

@admin_bp.route("/set-status/<userId>", methods=["PUT"])
@role_required("SUPER_ADMIN")
def set_status(userId):
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is missing.", 400)
        validated = UserStatusSchema(**data)
    except ValidationError as err:
        return error_response(f"Validation error: {err.errors()[0]['msg']}", 400)
    except Exception:
        return error_response("Invalid JSON format in body.", 400)
        
    return AuthService.set_user_status(userId, validated.active)

@admin_bp.route("/create-class", methods=["POST"])
@role_required("SUPER_ADMIN")
def create_class():
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is missing.", 400)
        validated = CreateClassSchema(**data)
    except ValidationError as err:
        return error_response(f"Validation error: {err.errors()[0]['msg']}", 400)
    except Exception:
        return error_response("Invalid JSON format in body.", 400)
        
    return SuperAdminService.create_class(
        class_name=validated.className,
        section=validated.section,
        class_teacher=validated.classTeacher
    )

@admin_bp.route("/create-subject", methods=["POST"])
@role_required("SUPER_ADMIN")
def create_subject():
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is missing.", 400)
        validated = CreateSubjectSchema(**data)
    except ValidationError as err:
        return error_response(f"Validation error: {err.errors()[0]['msg']}", 400)
    except Exception:
        return error_response("Invalid JSON format in body.", 400)
        
    return SuperAdminService.create_subject(validated.subjectName)

@admin_bp.route("/assign-teacher", methods=["POST"])
@role_required("SUPER_ADMIN")
def assign_teacher():
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is missing.", 400)
        validated = AssignTeacherSchema(**data)
    except ValidationError as err:
        return error_response(f"Validation error: {err.errors()[0]['msg']}", 400)
    except Exception:
        return error_response("Invalid JSON format in body.", 400)
        
    return SuperAdminService.assign_teacher(validated.teacherId, validated.classId)
