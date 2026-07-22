from flask import Blueprint, request
from pydantic import ValidationError
from middleware.role_required import role_required
from flask_jwt_extended import get_jwt_identity
from services.fees_service import FeesService
from models.fees_model import (
    CreateFeeStructureSchema,
    UpdateFeeStructureSchema,
    RecordPaymentSchema,
    SendReminderSchema
)
from utils.response import error_response

fees_bp = Blueprint("fees", __name__)

# --- SUPER ADMIN APIs ---

@fees_bp.route("/api/admin/fees", methods=["POST"])
@role_required("SUPER_ADMIN")
def create_fee_structure():
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is missing.", 400)
        validated = CreateFeeStructureSchema(**data)
    except ValidationError as err:
        return error_response(f"Validation error: {err.errors()[0]['msg']}", 400)
    except Exception:
        return error_response("Invalid JSON format in body.", 400)
        
    current_user_id = get_jwt_identity()
    return FeesService.create_fee_structure(
        title=validated.title,
        academic_year=validated.academicYear,
        class_ids=validated.classIds,
        fee_items=[item.model_dump() for item in validated.feeItems],
        due_date=validated.dueDate,
        created_by=current_user_id
    )

@fees_bp.route("/api/admin/fees", methods=["GET"])
@role_required("SUPER_ADMIN")
def get_fee_structures():
    academic_year = request.args.get("academicYear")
    class_id = request.args.get("classId") or request.args.get("class")
    status = request.args.get("status")
    return FeesService.get_fee_structures(academic_year, class_id, status)

@fees_bp.route("/api/admin/fees/<feeStructureId>", methods=["GET"])
@role_required("SUPER_ADMIN")
def get_fee_structure(feeStructureId):
    return FeesService.get_fee_structure(feeStructureId)

@fees_bp.route("/api/admin/fees/<feeStructureId>", methods=["PUT"])
@role_required("SUPER_ADMIN")
def update_fee_structure(feeStructureId):
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is missing.", 400)
        validated = UpdateFeeStructureSchema(**data)
    except ValidationError as err:
        return error_response(f"Validation error: {err.errors()[0]['msg']}", 400)
    except Exception:
        return error_response("Invalid JSON format in body.", 400)
        
    return FeesService.update_fee_structure(
        fee_structure_id=feeStructureId,
        title=validated.title,
        academic_year=validated.academicYear,
        class_ids=validated.classIds,
        fee_items=[item.model_dump() for item in validated.feeItems],
        due_date=validated.dueDate
    )

@fees_bp.route("/api/admin/fees/<feeStructureId>", methods=["DELETE"])
@role_required("SUPER_ADMIN")
def delete_fee_structure(feeStructureId):
    return FeesService.delete_fee_structure(feeStructureId)

@fees_bp.route("/api/admin/fees/dashboard", methods=["GET"])
@role_required("SUPER_ADMIN")
def get_dashboard():
    return FeesService.get_dashboard()

@fees_bp.route("/api/admin/fees/students", methods=["GET"])
@role_required("SUPER_ADMIN")
def get_student_fee_list():
    class_id = request.args.get("classId") or request.args.get("class")
    status = request.args.get("status")
    student_name = request.args.get("studentName") or request.args.get("name")
    return FeesService.get_student_fee_list(class_id, status, student_name)

@fees_bp.route("/api/admin/fees/reminder", methods=["POST"])
@role_required("SUPER_ADMIN")
def send_fee_reminder():
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is missing.", 400)
        validated = SendReminderSchema(**data)
    except ValidationError as err:
        return error_response(f"Validation error: {err.errors()[0]['msg']}", 400)
    except Exception:
        return error_response("Invalid JSON format in body.", 400)
        
    return FeesService.send_reminders(validated.studentIds, validated.message)

@fees_bp.route("/api/admin/fees/payment", methods=["POST"])
@role_required("SUPER_ADMIN")
def record_fee_payment():
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is missing.", 400)
        validated = RecordPaymentSchema(**data)
    except ValidationError as err:
        return error_response(f"Validation error: {err.errors()[0]['msg']}", 400)
    except Exception:
        return error_response("Invalid JSON format in body.", 400)
        
    current_user_id = get_jwt_identity()
    return FeesService.record_payment(
        student_id=validated.studentId,
        fee_structure_id=validated.feeStructureId,
        amount=validated.amount,
        payment_mode=validated.paymentMode,
        transaction_id=validated.transactionId,
        received_by=current_user_id
    )

@fees_bp.route("/api/admin/fees/payments", methods=["GET"])
@role_required("SUPER_ADMIN")
def get_payment_history_admin():
    student_id = request.args.get("studentId") or request.args.get("student")
    class_id = request.args.get("classId") or request.args.get("class")
    date = request.args.get("date")
    payment_mode = request.args.get("paymentMode")
    return FeesService.get_payment_history(student_id, class_id, date, payment_mode)

# --- TEACHER APIs ---

@fees_bp.route("/api/teacher/fees", methods=["GET"])
@role_required("TEACHER")
def get_teacher_fees_overview():
    current_user_id = get_jwt_identity()
    search = request.args.get("search")
    status = request.args.get("status")
    return FeesService.get_teacher_overview(current_user_id, search, status)

@fees_bp.route("/api/teacher/fees/<studentId>", methods=["GET"])
@role_required("TEACHER")
def get_teacher_student_fees_details(studentId):
    current_user_id = get_jwt_identity()
    return FeesService.get_teacher_student_details(current_user_id, studentId)

# --- STUDENT APIs ---

@fees_bp.route("/api/student/fees", methods=["GET"])
@role_required("STUDENT")
def get_student_fees_my():
    current_user_id = get_jwt_identity()
    return FeesService.get_student_fees(current_user_id)

@fees_bp.route("/api/student/fees/payments", methods=["GET"])
@role_required("STUDENT")
def get_student_payments_my():
    current_user_id = get_jwt_identity()
    return FeesService.get_student_payments(current_user_id)

@fees_bp.route("/api/student/fees/notifications", methods=["GET"])
@role_required("STUDENT")
def get_student_notifications_my():
    current_user_id = get_jwt_identity()
    return FeesService.get_student_notifications(current_user_id)
