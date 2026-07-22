import os
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import Config
from database.mongodb import db_wrapper
from middleware.jwt_auth import init_jwt_callbacks
from utils.helpers import hash_password
from utils.response import error_response

# Import routes/blueprints
from routes.auth import auth_bp
from routes.super_admin import admin_bp
from routes.teacher import teacher_bp
from routes.student import student_bp
from routes.marks import marks_bp
from routes.classes import classes_bp
from routes.subjects import subjects_bp
from routes.exams import exams_bp
from routes.discussions import discussions_bp
from routes.fees import fees_bp
from routes.online_exams import online_exams_bp



def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize CORS
    CORS(app)

    # Initialize MongoDB Client & wrapper
    db = db_wrapper.init_app(app)

    # Initialize JWT Manager
    jwt = JWTManager(app)
    init_jwt_callbacks(jwt)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(marks_bp)
    app.register_blueprint(classes_bp)
    app.register_blueprint(subjects_bp)
    app.register_blueprint(exams_bp)
    app.register_blueprint(discussions_bp)
    app.register_blueprint(fees_bp)
    app.register_blueprint(online_exams_bp)
    @app.route("/")

    def home():
        return "Hello, World!"
    # Error handling
    @app.errorhandler(404)
    def not_found_error(error):
        return error_response("Endpoint not found.", 404)

    @app.errorhandler(500)
    def internal_error(error):
        return error_response(f"Internal server error: {str(error)}", 500)

    # JWT Error handlers for custom response shape
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return error_response("The access token has expired.", 401)

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return error_response("Signature verification failed.", 401)

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return error_response("Request does not contain a valid JWT access token.", 401)

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return error_response("This token has been logged out and revoked.", 401)

    # Seed Database
    try:
        seed_database(app)
    except Exception as e:
        print(f"Warning: Could not seed database on startup: {e}")

    return app

def seed_database(app):
    """Seeds the default SUPER_ADMIN account if no super admin exists in database."""
    db = app.db
    if db is None:
        return
        
    admin_id = app.config.get("DEFAULT_ADMIN_USER_ID", "admin")
    admin_pwd = app.config.get("DEFAULT_ADMIN_PASSWORD", "Admin@123")
    
    try:
        # 1. Ensure the user specified in environment variables is seeded
        config_admin = db.users.find_one({"userId": admin_id})
        if not config_admin:
            hashed = hash_password(admin_pwd)
            db.users.insert_one({
                "userId": admin_id,
                "password": hashed,
                "role": "SUPER_ADMIN",
                "active": True,
                "createdAt": None
            })
            print("="*65)
            print(f"DATABASE SEEDER: Default SUPER_ADMIN user has been successfully created.")
            print(f"Username: {admin_id}")
            print(f"Password: {admin_pwd}")
            print("="*65)

        # 2. Guarantee that the 'admin' ID required by the spec exists
        if admin_id != "admin":
            spec_admin = db.users.find_one({"userId": "admin"})
            if not spec_admin:
                hashed = hash_password("Admin@123")
                db.users.insert_one({
                    "userId": "admin",
                    "password": hashed,
                    "role": "SUPER_ADMIN",
                    "active": True,
                    "createdAt": None
                })
                print("="*65)
                print(f"DATABASE SEEDER: Spec required SUPER_ADMIN user 'admin' has been successfully created.")
                print(f"Username: admin")
                print(f"Password: Admin@123")
                print("="*65)
    except Exception as e:
        print(f"Warning: Database seeding skipped due to connection error: {e}")


app = create_app()

if __name__ == "__main__":
    port = app.config.get("PORT", 5000)
    app.run(host="0.0.0.0", port=port, debug=True)
