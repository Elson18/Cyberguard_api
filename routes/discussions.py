from flask import Blueprint, request
from pydantic import ValidationError
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from middleware.role_required import role_required
from models.discussion_model import CreateDiscussionSchema, SendReplySchema, ChangeStatusSchema
from services.discussion_service import DiscussionService
from utils.response import error_response

discussions_bp = Blueprint("discussions", __name__)

# --- STUDENT ROUTES ---

@discussions_bp.route("/api/discussions", methods=["POST"])
@role_required("STUDENT")
def create_discussion():
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is missing.", 400)
        validated = CreateDiscussionSchema(**data)
    except ValidationError as err:
        return error_response(f"Validation error: {err.errors()[0]['msg']}", 400)
    except Exception:
        return error_response("Invalid JSON format in body.", 400)

    current_user_id = get_jwt_identity()
    return DiscussionService.create_discussion(current_user_id, validated.model_dump())

@discussions_bp.route("/api/student/discussions", methods=["GET"])
@role_required("STUDENT")
def get_student_discussions():
    current_user_id = get_jwt_identity()
    status_filter = request.args.get("status")
    priority_filter = request.args.get("priority")
    return DiscussionService.get_student_discussions(current_user_id, status_filter, priority_filter)

@discussions_bp.route("/api/discussions/<discussionId>", methods=["GET"])
@role_required("STUDENT")
def get_discussion_details(discussionId):
    current_user_id = get_jwt_identity()
    return DiscussionService.get_discussion_details(current_user_id, "STUDENT", discussionId)

@discussions_bp.route("/api/discussions/<discussionId>/reply", methods=["POST"])
@role_required("STUDENT")
def send_student_reply(discussionId):
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is missing.", 400)
        validated = SendReplySchema(**data)
    except ValidationError as err:
        return error_response(f"Validation error: {err.errors()[0]['msg']}", 400)
    except Exception:
        return error_response("Invalid JSON format in body.", 400)

    current_user_id = get_jwt_identity()
    return DiscussionService.send_student_reply(current_user_id, discussionId, validated.message)

@discussions_bp.route("/api/discussions/<discussionId>", methods=["DELETE"])
@role_required("STUDENT")
def delete_student_discussion(discussionId):
    current_user_id = get_jwt_identity()
    return DiscussionService.delete_student_discussion(current_user_id, discussionId)


# --- TEACHER ROUTES ---

@discussions_bp.route("/api/teacher/discussions", methods=["GET"])
@role_required("TEACHER")
def get_teacher_discussions():
    current_user_id = get_jwt_identity()
    class_id = request.args.get("classId")
    status = request.args.get("status")
    category = request.args.get("category")
    priority = request.args.get("priority")
    return DiscussionService.get_teacher_discussions(current_user_id, class_id, status, category, priority)

@discussions_bp.route("/api/teacher/discussions/<discussionId>", methods=["GET"])
@role_required("TEACHER")
def get_teacher_discussion_details(discussionId):
    current_user_id = get_jwt_identity()
    return DiscussionService.get_discussion_details(current_user_id, "TEACHER", discussionId)

@discussions_bp.route("/api/teacher/discussions/<discussionId>/reply", methods=["POST"])
@role_required("TEACHER")
def send_teacher_reply(discussionId):
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is missing.", 400)
        validated = SendReplySchema(**data)
    except ValidationError as err:
        return error_response(f"Validation error: {err.errors()[0]['msg']}", 400)
    except Exception:
        return error_response("Invalid JSON format in body.", 400)

    current_user_id = get_jwt_identity()
    return DiscussionService.send_teacher_reply(current_user_id, discussionId, validated.message)

@discussions_bp.route("/api/teacher/discussions/<discussionId>/status", methods=["PUT"])
@role_required("TEACHER")
def change_teacher_discussion_status(discussionId):
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is missing.", 400)
        validated = ChangeStatusSchema(**data)
    except ValidationError as err:
        return error_response(f"Validation error: {err.errors()[0]['msg']}", 400)
    except Exception:
        return error_response("Invalid JSON format in body.", 400)

    current_user_id = get_jwt_identity()
    return DiscussionService.change_discussion_status(current_user_id, "TEACHER", discussionId, validated.status)


# --- SUPER ADMIN ROUTES ---

@discussions_bp.route("/api/admin/discussions", methods=["GET"])
@role_required("SUPER_ADMIN")
def get_admin_discussions():
    school = request.args.get("School") or request.args.get("school")
    class_id = request.args.get("Class") or request.args.get("class") or request.args.get("classId")
    teacher_id = request.args.get("Teacher") or request.args.get("teacher") or request.args.get("teacherId")
    student_id = request.args.get("Student") or request.args.get("student") or request.args.get("studentId")
    status = request.args.get("Status") or request.args.get("status")
    category = request.args.get("Category") or request.args.get("category")
    priority = request.args.get("Priority") or request.args.get("priority")

    return DiscussionService.get_all_discussions(
        school=school,
        class_id=class_id,
        teacher_id=teacher_id,
        student_id=student_id,
        status=status,
        category=category,
        priority=priority
    )

@discussions_bp.route("/api/admin/discussions/<discussionId>", methods=["GET"])
@role_required("SUPER_ADMIN")
def get_admin_discussion_details(discussionId):
    current_user_id = get_jwt_identity()
    return DiscussionService.get_discussion_details(current_user_id, "SUPER_ADMIN", discussionId)

@discussions_bp.route("/api/admin/discussions/<discussionId>/reply", methods=["POST"])
@role_required("SUPER_ADMIN")
def send_admin_reply(discussionId):
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is missing.", 400)
        validated = SendReplySchema(**data)
    except ValidationError as err:
        return error_response(f"Validation error: {err.errors()[0]['msg']}", 400)
    except Exception:
        return error_response("Invalid JSON format in body.", 400)

    current_user_id = get_jwt_identity()
    return DiscussionService.send_admin_reply(current_user_id, discussionId, validated.message)

@discussions_bp.route("/api/admin/discussions/<discussionId>/status", methods=["PUT"])
@role_required("SUPER_ADMIN")
def change_admin_discussion_status(discussionId):
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is missing.", 400)
        validated = ChangeStatusSchema(**data)
    except ValidationError as err:
        return error_response(f"Validation error: {err.errors()[0]['msg']}", 400)
    except Exception:
        return error_response("Invalid JSON format in body.", 400)

    current_user_id = get_jwt_identity()
    return DiscussionService.change_discussion_status(current_user_id, "SUPER_ADMIN", discussionId, validated.status)

@discussions_bp.route("/api/admin/discussions/<discussionId>", methods=["DELETE"])
@role_required("SUPER_ADMIN")
def delete_admin_discussion(discussionId):
    return DiscussionService.delete_admin_discussion(discussionId)


# --- COMMON ROUTES ---

@discussions_bp.route("/api/discussions/statistics", methods=["GET"])
@jwt_required()
def get_discussion_statistics():
    return DiscussionService.get_statistics()
