from pydantic import BaseModel, Field
from typing import Optional

class CreateTeacherSchema(BaseModel):
    userId: str = Field(..., min_length=3, max_length=50, description="Unique login ID for the teacher.")
    password: str = Field(..., min_length=6, description="Login password.")
    name: str = Field(..., min_length=2, max_length=100, description="Full name of the teacher.")
    department: str = Field(..., min_length=2, max_length=100, description="Teacher's department.")
    teacherId: Optional[str] = Field(None, description="Optional custom unique teacher ID. If not provided, it will match userId.")
