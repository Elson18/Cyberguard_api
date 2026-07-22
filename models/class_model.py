from pydantic import BaseModel, Field
from typing import Optional

class CreateClassSchema(BaseModel):
    className: str = Field(..., min_length=1, max_length=50, description="Name of the class, e.g., Grade 10.")
    section: str = Field(..., min_length=1, max_length=10, description="Section of the class, e.g., A.")
    classTeacher: Optional[str] = Field(None, description="teacherId of the class teacher.")
