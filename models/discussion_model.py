from pydantic import BaseModel, Field, field_validator
from typing import Optional

class CreateDiscussionSchema(BaseModel):
    title: str = Field(..., min_length=1, description="Title of the discussion.")
    category: str = Field(..., description="Category of the discussion.")
    priority: str = Field(..., description="Priority of the discussion.")
    message: str = Field(..., min_length=1, description="Initial message of the discussion.")

    @field_validator('title', 'message')
    @classmethod
    def check_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace only.")
        return v.strip()

    @field_validator('category')
    @classmethod
    def validate_category(cls, v: str) -> str:
        upper_v = v.upper().strip()
        allowed = ["ACADEMIC", "ASSIGNMENT", "ATTENDANCE", "EXAMINATION", "TECHNICAL", "GENERAL", "OTHER"]
        if upper_v not in allowed:
            raise ValueError(f"Invalid category. Allowed values: {', '.join(allowed)}")
        return upper_v

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v: str) -> str:
        upper_v = v.upper().strip()
        allowed = ["LOW", "MEDIUM", "HIGH"]
        if upper_v not in allowed:
            raise ValueError(f"Invalid priority. Allowed values: {', '.join(allowed)}")
        return upper_v

class SendReplySchema(BaseModel):
    message: str = Field(..., min_length=1, description="Message body of the reply.")

    @field_validator('message')
    @classmethod
    def check_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Message cannot be empty or whitespace only.")
        return v.strip()

class ChangeStatusSchema(BaseModel):
    status: str = Field(..., description="Status to update.")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        upper_v = v.upper().strip()
        allowed = ["OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"]
        if upper_v not in allowed:
            raise ValueError(f"Invalid status. Allowed values: {', '.join(allowed)}")
        return upper_v
