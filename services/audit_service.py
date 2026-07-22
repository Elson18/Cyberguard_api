from datetime import datetime, timezone
from database.mongodb import db_wrapper

class AuditService:
    @staticmethod
    def log_action(action: str, performed_by: str, role: str, details: dict = None):
        """Logs crucial system operations to the audit_logs collection."""
        db = db_wrapper.db
        if db is None:
            return False
            
        try:
            log_doc = {
                "action": action,
                "performedBy": performed_by,
                "role": role,
                "details": details or {},
                "timestamp": datetime.now(timezone.utc)
            }
            db.audit_logs.insert_one(log_doc)
            return True
        except Exception as e:
            print(f"Error logging audit trail: {e}")
            return False
