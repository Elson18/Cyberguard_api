from pydantic import BaseModel, Field

class CreateMarksSchema(BaseModel):
    studentId: str = Field(..., description="studentId of the student.")
    classId: str = Field(..., description="classId (string ID) of the class.")
    subjectId: str = Field(..., description="subjectId (string ID) of the subject.")
    exam: str = Field(..., description="Name of the exam, e.g., Midterm, Final.")
    marks: float = Field(..., ge=0, le=100, description="Marks scored, between 0 and 100.")
    academicYear: str = Field(..., description="Academic year, e.g., 2026.")

class UpdateMarksSchema(BaseModel):
    marks: float = Field(..., ge=0, le=100, description="Updated marks scored, between 0 and 100.")

class PublishMarksSchema(BaseModel):
    classId: str = Field(..., description="classId of the class to publish marks for.")
    exam: str = Field(..., description="Name of the exam to publish marks for.")
    academicYear: str = Field(..., description="Academic year to publish marks for.")
