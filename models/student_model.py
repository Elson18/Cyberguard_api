from pydantic import BaseModel, Field
from typing import Optional

class CreateStudentSchema(BaseModel):
    userId: str = Field(..., min_length=3, max_length=50, description="Unique login ID for the student.")
    password: str = Field(..., min_length=6, description="Login password.")
    name: str = Field(..., min_length=2, max_length=100, description="Full name of the student.")
    classId: str = Field(..., description="ID of the class the student is enrolled in.")
    rollNumber: str = Field(..., description="Roll number in the class.")
    studentId: Optional[str] = Field(None, description="Optional custom student ID. If not provided, it will match userId.")
