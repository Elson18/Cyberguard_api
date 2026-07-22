from pydantic import BaseModel, Field

class CreateSubjectSchema(BaseModel):
    subjectName: str = Field(..., min_length=2, max_length=100, description="Name of the subject, e.g., Mathematics.")
