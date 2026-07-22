from flask import Blueprint, request
from pydantic import ValidationError
from models.user_model import UserLoginSchema, ChangePasswordSchema
from services.auth_service import AuthService
from utils.response import error_response
from flask_jwt_extended import jwt_required, get_jwt_identity

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is missing.", 400)
        validated = UserLoginSchema(**data)
    except ValidationError as err:
        # Return clean error message
        return error_response(f"Validation error: {err.errors()[0]['msg']}", 400)
    except Exception:
        return error_response("Invalid JSON format in body.", 400)
        
    return AuthService.login(validated.userId, validated.password)

@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    return AuthService.logout()

@auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    current_user_id = get_jwt_identity()
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is missing.", 400)
        validated = ChangePasswordSchema(**data)
    except ValidationError as err:
        return error_response(f"Validation error: {err.errors()[0]['msg']}", 400)
    except Exception:
        return error_response("Invalid JSON format in body.", 400)
        
    return AuthService.change_password(current_user_id, validated.oldPassword, validated.newPassword)
