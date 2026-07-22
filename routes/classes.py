from flask import Blueprint
from database.mongodb import db_wrapper
from flask_jwt_extended import jwt_required
from utils.response import success_response, error_response
from utils.helpers import serialize_doc

classes_bp = Blueprint("classes", __name__, url_prefix="/api/classes")

@classes_bp.route("", methods=["GET"])
@jwt_required()
def get_all_classes():
    """Returns a list of all classes. Protected by JWT."""
    db = db_wrapper.db
    if db is None:
        return error_response("Database connection not ready.", 500)
    classes = list(db.classes.find({}))
    return success_response(data=serialize_doc(classes))
