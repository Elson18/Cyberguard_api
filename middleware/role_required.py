from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from utils.response import error_response

def role_required(*allowed_roles):
    """
    Decorator to restrict access to endpoints based on user roles stored in the JWT.
    Accepts a list of permitted roles (e.g., 'SUPER_ADMIN', 'TEACHER', 'STUDENT').
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Ensure JWT is present in request
            verify_jwt_in_request()
            
            # Retrieve roles claim
            claims = get_jwt()
            user_role = claims.get("role")
            
            if not user_role or user_role not in allowed_roles:
                return error_response(f"Access denied. Required roles: {', '.join(allowed_roles)}", 403)
                
            return fn(*args, **kwargs)
        return wrapper
    return decorator
