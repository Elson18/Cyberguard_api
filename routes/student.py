import io
from flask import Blueprint, request, send_file
from database.mongodb import db_wrapper
from middleware.role_required import role_required
from services.report_service import ReportService
from utils.response import error_response
from flask_jwt_extended import get_jwt_identity

student_bp = Blueprint("student", __name__, url_prefix="/api/student")

def get_student_id_from_identity(user_id):
    db = db_wrapper.db
    if db is None:
        return None
    student = db.students.find_one({"userId": user_id})
    return student.get("studentId") if student else None

@student_bp.route("/profile", methods=["GET"])
@role_required("STUDENT")
def get_profile():
    """Allows students to view their own profile, including class details."""
    current_user_id = get_jwt_identity()
    return ReportService.get_student_profile(current_user_id)

@student_bp.route("/dashboard", methods=["GET"])
@role_required("STUDENT")
def get_dashboard():
    """Returns student profile, latest published exam report card, and summaries."""
    current_user_id = get_jwt_identity()
    return ReportService.get_student_dashboard(current_user_id)

@student_bp.route("/marks", methods=["GET"])
@role_required("STUDENT")
def get_marks():
    """Allows students to view their marks, filtered optionally by exam, academicYear, or examId."""
    current_user_id = get_jwt_identity()
    student_id = get_student_id_from_identity(current_user_id)
    if not student_id:
        return error_response("Student profile not found.", 404)
        
    exam = request.args.get("exam")
    academic_year = request.args.get("academicYear")
    exam_id = request.args.get("examId")
    return ReportService.get_student_marks(student_id, exam, academic_year, exam_id)

@student_bp.route("/report-card", methods=["GET"])
@role_required("STUDENT")
def get_report_card():
    """Allows students to view their report cards once published, with optional filters."""
    current_user_id = get_jwt_identity()
    student_id = get_student_id_from_identity(current_user_id)
    if not student_id:
        return error_response("Student profile not found.", 404)
        
    exam = request.args.get("exam")
    academic_year = request.args.get("academicYear")
    exam_id = request.args.get("examId")
    return ReportService.get_student_report_card(student_id, exam, academic_year, exam_id)

@student_bp.route("/rank", methods=["GET"])
@role_required("STUDENT")
def get_rank():
    """Allows students to view their ranking and overall scores once published."""
    current_user_id = get_jwt_identity()
    student_id = get_student_id_from_identity(current_user_id)
    if not student_id:
        return error_response("Student profile not found.", 404)
        
    exam = request.args.get("exam")
    academic_year = request.args.get("academicYear")
    exam_id = request.args.get("examId")
    return ReportService.get_student_rank(student_id, exam, academic_year, exam_id)

@student_bp.route("/report-card/pdf/<examId>", methods=["GET"])
@role_required("STUDENT")
def get_pdf_report_card(examId):
    """Generates and downloads a professional PDF report card for a published exam."""
    current_user_id = get_jwt_identity()
    pdf_bytes, err_msg, status_code = ReportService.get_pdf_report_card(current_user_id, examId)
    
    if err_msg:
        return error_response(err_msg, status_code)
        
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"Report_Card_{examId}.pdf"
    )
