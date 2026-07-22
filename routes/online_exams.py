from flask import Blueprint, request
from pydantic import ValidationError
from flask_jwt_extended import get_jwt_identity
from middleware.role_required import role_required
from services.online_exam_service import OnlineExamService
from models.online_exam_model import CreateOnlineExamSchema, UpdateOnlineExamSchema, SaveAnswerSchema
from utils.response import error_response

online_exams_bp = Blueprint("online_exams", __name__, url_prefix="/api")

# ==========================================
# SUPER ADMIN ROUTE HANDLERS
# ==========================================

@online_exams_bp.route("/admin/exams", methods=["POST"])
@role_required("SUPER_ADMIN")
def admin_create_exam():
    admin_user_id = get_jwt_identity()
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is missing.", 400)
        validated = CreateOnlineExamSchema(**data)
    except ValidationError as err:
        return error_response(f"Validation error: {err.errors()[0]['msg']}", 400)
    except Exception as e:
        return error_response(f"Invalid JSON format in body: {str(e)}", 400)
        
    return OnlineExamService.create_exam(admin_user_id, validated.model_dump())

@online_exams_bp.route("/admin/exams/<examId>", methods=["PUT"])
@role_required("SUPER_ADMIN")
def admin_update_exam(examId):
    admin_user_id = get_jwt_identity()
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is missing.", 400)
        validated = UpdateOnlineExamSchema(**data)
    except ValidationError as err:
        return error_response(f"Validation error: {err.errors()[0]['msg']}", 400)
    except Exception as e:
        return error_response(f"Invalid JSON format in body: {str(e)}", 400)
        
    return OnlineExamService.update_exam(admin_user_id, examId, validated.model_dump(exclude_unset=True))

@online_exams_bp.route("/admin/exams/<examId>", methods=["DELETE"])
@role_required("SUPER_ADMIN")
def admin_delete_exam(examId):
    admin_user_id = get_jwt_identity()
    return OnlineExamService.delete_exam(admin_user_id, examId)

@online_exams_bp.route("/admin/exams/<examId>/publish", methods=["POST"])
@role_required("SUPER_ADMIN")
def admin_publish_exam(examId):
    admin_user_id = get_jwt_identity()
    return OnlineExamService.publish_exam(admin_user_id, examId)

@online_exams_bp.route("/admin/exams/<examId>/close", methods=["POST"])
@role_required("SUPER_ADMIN")
def admin_close_exam(examId):
    admin_user_id = get_jwt_identity()
    return OnlineExamService.close_exam(admin_user_id, examId)

@online_exams_bp.route("/admin/exams", methods=["GET"])
@role_required("SUPER_ADMIN")
def admin_get_exams():
    filters = {
        "classId": request.args.get("classId"),
        "subjectId": request.args.get("subjectId"),
        "academicYear": request.args.get("academicYear"),
        "status": request.args.get("status")
    }
    return OnlineExamService.get_exams_admin(filters)

@online_exams_bp.route("/admin/exams/<examId>", methods=["GET"])
@role_required("SUPER_ADMIN")
def admin_get_exam_by_id(examId):
    return OnlineExamService.get_exam_by_id_admin(examId)

@online_exams_bp.route("/admin/exams/<examId>/publish-results", methods=["POST"])
@role_required("SUPER_ADMIN")
def admin_publish_results(examId):
    admin_user_id = get_jwt_identity()
    return OnlineExamService.publish_results(admin_user_id, examId)


# ==========================================
# TEACHER ROUTE HANDLERS
# ==========================================

@online_exams_bp.route("/teacher/exams", methods=["GET"])
@role_required("TEACHER")
def teacher_get_exams():
    teacher_user_id = get_jwt_identity()
    return OnlineExamService.get_exams_teacher(teacher_user_id)

@online_exams_bp.route("/teacher/exams/<examId>/live", methods=["GET"])
@role_required("TEACHER")
def teacher_get_live_monitoring(examId):
    teacher_user_id = get_jwt_identity()
    return OnlineExamService.get_live_monitoring(teacher_user_id, examId)

@online_exams_bp.route("/teacher/exams/<examId>/attempts", methods=["GET"])
@role_required("TEACHER")
def teacher_get_attempts(examId):
    teacher_user_id = get_jwt_identity()
    return OnlineExamService.get_attempts(teacher_user_id, examId)

@online_exams_bp.route("/teacher/exams/<examId>/publish-results", methods=["POST"])
@role_required("TEACHER")
def teacher_publish_results(examId):
    teacher_user_id = get_jwt_identity()
    return OnlineExamService.publish_results_teacher(teacher_user_id, examId)



# ==========================================
# STUDENT ROUTE HANDLERS
# ==========================================

@online_exams_bp.route("/student/exams", methods=["GET"])
@role_required("STUDENT")
def student_get_exams():
    student_user_id = get_jwt_identity()
    filters = {
        "academicYear": request.args.get("academicYear")
    }
    return OnlineExamService.get_exams_student(student_user_id, filters)

@online_exams_bp.route("/student/exams/<examId>/start", methods=["POST"])
@role_required("STUDENT")
def student_start_exam(examId):
    student_user_id = get_jwt_identity()
    return OnlineExamService.start_exam(student_user_id, examId)

@online_exams_bp.route("/student/exams/<examId>", methods=["GET"])
@role_required("STUDENT")
def student_get_questions(examId):
    student_user_id = get_jwt_identity()
    return OnlineExamService.get_exam_questions(student_user_id, examId)

@online_exams_bp.route("/student/exams/<examId>/save-answer", methods=["POST"])
@role_required("STUDENT")
def student_save_answer(examId):
    student_user_id = get_jwt_identity()
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is missing.", 400)
        validated = SaveAnswerSchema(**data)
    except ValidationError as err:
        return error_response(f"Validation error: {err.errors()[0]['msg']}", 400)
    except Exception as e:
        return error_response(f"Invalid JSON format in body: {str(e)}", 400)
        
    return OnlineExamService.save_answer(student_user_id, examId, validated.model_dump())

@online_exams_bp.route("/student/exams/<examId>/submit", methods=["POST"])
@role_required("STUDENT")
def student_submit_exam(examId):
    student_user_id = get_jwt_identity()
    return OnlineExamService.submit_exam(student_user_id, examId)

@online_exams_bp.route("/student/exams/<examId>/result", methods=["GET"])
@role_required("STUDENT")
def student_view_result(examId):
    student_user_id = get_jwt_identity()
    return OnlineExamService.view_result(student_user_id, examId)
