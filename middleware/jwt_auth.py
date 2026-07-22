from database.mongodb import db_wrapper

def init_jwt_callbacks(jwt):
    """
    Registers custom callback handlers for Flask-JWT-Extended.
    E.g. token blocklist lookup for secure logout.
    """
    @jwt.token_in_blocklist_loader
    def check_if_token_is_revoked(jwt_header, jwt_payload: dict):
        jti = jwt_payload["jti"]
        db = db_wrapper.db
        if db is None:
            return False
            
        token = db.token_blocklist.find_one({"jti": jti})
        return token is not None
