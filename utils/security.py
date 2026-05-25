from fastapi import Header, HTTPException


def optional_user_id(x_user_id: str | None = Header(None, alias="X-User-Id")) -> str | None:
    """Optional user id from extension or web frontend."""
    if x_user_id and len(x_user_id.strip()) > 0:
        return x_user_id.strip()
    return None


def require_user_id(x_user_id: str | None = Header(None, alias="X-User-Id")) -> str:
    user_id = optional_user_id(x_user_id)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user_id
