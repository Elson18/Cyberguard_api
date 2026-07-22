from flask import Blueprint, request
from database.mongodb import db_wrapper
from middleware.role_required import role_required
from utils.response import success_response, error_response
from utils.helpers import serialize_doc
from flask_jwt_extended import get_jwt_identity
from bson import ObjectId

teacher_bp = Blueprint("teacher", __name__, url_prefix="/api/teacher")

@teacher_bp.route("/classes", methods=["GET"])
@role_required("TEACHER")
def get_classes():
    """Returns all classes assigned to the logged-in teacher."""
    current_user_id = get_jwt_identity()
    db = db_wrapper.db
    if db is None:
        return error_response("Database connection not ready.", 500)
        
    teacher = db.teachers.find_one({"userId": current_user_id})
    if not teacher:
        return error_response("Teacher profile not found.", 404)
        
    assigned_class_ids = teacher.get("assignedClasses", [])
    
    # Resolve class documents
    classes_list = []
    for cid in assigned_class_ids:
        class_filter = {"_id": cid}
        if ObjectId.is_valid(str(cid)):
            try:
                class_filter = {"$or": [{"_id": cid}, {"_id": ObjectId(cid)}]}
            except Exception:
                pass
        cls = db.classes.find_one(class_filter)
        if cls:
            classes_list.append(cls)
            
    return success_response(data=serialize_doc(classes_list))

@teacher_bp.route("/students/<classId>", methods=["GET"])
@role_required("TEACHER")
def get_students(classId):
    """Returns all students belonging to classId, after verifying assignment."""
    current_user_id = get_jwt_identity()
    db = db_wrapper.db
    if db is None:
        return error_response("Database connection not ready.", 500)
        
    teacher = db.teachers.find_one({"userId": current_user_id})
    if not teacher:
        return error_response("Teacher profile not found.", 404)
        
    assigned_class_ids = teacher.get("assignedClasses", [])
    if classId not in assigned_class_ids:
        return error_response("Access denied. You are not assigned to this class.", 403)
        
    students = list(db.students.find({"classId": classId}))
    return success_response(data=serialize_doc(students))

@teacher_bp.route("/rankings/<classId>", methods=["GET"])
@role_required("TEACHER")
def get_rankings(classId):
    """Returns the computed rankings list for classId, exam, and academicYear."""
    current_user_id = get_jwt_identity()
    db = db_wrapper.db
    if db is None:
        return error_response("Database connection not ready.", 500)
        
    exam = request.args.get("exam")
    academic_year = request.args.get("academicYear")
    if not exam or not academic_year:
        return error_response("Missing query parameters 'exam' or 'academicYear'.", 400)
        
    teacher = db.teachers.find_one({"userId": current_user_id})
    if not teacher:
        return error_response("Teacher profile not found.", 404)
        
    assigned_class_ids = teacher.get("assignedClasses", [])
    if classId not in assigned_class_ids:
        return error_response("Access denied. You are not assigned to this class.", 403)
        
    rankings = list(db.report_cards.find({
        "classId": classId,
        "exam": exam,
        "academicYear": academic_year
    }).sort("rank", 1))
    
    return success_response(data=serialize_doc(rankings))
