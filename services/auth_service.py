from datetime import datetime, timezone
from flask_jwt_extended import create_access_token, get_jwt
from database.mongodb import db_wrapper
from utils.helpers import check_password, hash_password
from utils.response import success_response, error_response

class AuthService:
    @staticmethod
    def login(user_id, password):
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        user = db.users.find_one({"userId": user_id})
        if not user:
            return error_response("Invalid credentials.", 401)
            
        if not user.get("active", True):
            return error_response("Your account has been deactivated. Please contact support.", 403)
            
        if not check_password(password, user["password"]):
            return error_response("Invalid credentials.", 401)
            
        # Generate JWT with custom role claim
        user_role = str(user.get("role", "")).upper()
        additional_claims = {
            "userId": user["userId"],
            "role": user_role
        }
        access_token = create_access_token(identity=user_id, additional_claims=additional_claims)
        
        # Build user profile context
        profile = {"userId": user["userId"], "role": user["role"]}
        if user["role"] == "TEACHER":
            teacher = db.teachers.find_one({"userId": user["userId"]})
            if teacher:
                profile["name"] = teacher.get("name")
                profile["teacherId"] = teacher.get("teacherId")
                profile["department"] = teacher.get("department")
                profile["assignedClasses"] = teacher.get("assignedClasses", [])
        elif user["role"] == "STUDENT":
            student = db.students.find_one({"userId": user["userId"]})
            if student:
                profile["name"] = student.get("name")
                profile["studentId"] = student.get("studentId")
                profile["classId"] = student.get("classId")
                profile["rollNumber"] = student.get("rollNumber")
                
        return success_response(
            message="Login successful.",
            data={"token": access_token, "user": profile}
        )

    @staticmethod
    def logout():
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        claims = get_jwt()
        jti = claims.get("jti")
        exp = claims.get("exp")
        
        if not jti or not exp:
            return error_response("Invalid token claims.", 400)
            
        # Create blocklist entry that MongoDB will clean up after expiry
        expiration_time = datetime.fromtimestamp(exp, tz=timezone.utc)
        try:
            db.token_blocklist.insert_one({
                "jti": jti,
                "expiresAt": expiration_time,
                "createdAt": datetime.now(timezone.utc)
            })
            return success_response(message="Logout successful.")
        except Exception as e:
            return error_response(f"Logout failed: {str(e)}", 500)

    @staticmethod
    def change_password(current_user_id, old_password, new_password):
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        user = db.users.find_one({"userId": current_user_id})
        if not user:
            return error_response("User not found.", 404)
            
        if not check_password(old_password, user["password"]):
            return error_response("Current password is incorrect.", 400)
            
        hashed = hash_password(new_password)
        db.users.update_one({"userId": current_user_id}, {"$set": {"password": hashed}})
        return success_response(message="Password updated successfully.")

    @staticmethod
    def reset_password(user_id, new_password):
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        user = db.users.find_one({"userId": user_id})
        if not user:
            return error_response("User not found.", 404)
            
        hashed = hash_password(new_password)
        db.users.update_one({"userId": user_id}, {"$set": {"password": hashed}})
        return success_response(message=f"Password for user '{user_id}' reset successfully.")

    @staticmethod
    def set_user_status(user_id, active: bool):
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        user = db.users.find_one({"userId": user_id})
        if not user:
            return error_response("User not found.", 404)
            
        db.users.update_one({"userId": user_id}, {"$set": {"active": active}})
        status = "activated" if active else "deactivated"
        return success_response(message=f"User '{user_id}' has been {status} successfully.")
