from pydantic import BaseModel, Field, model_validator, field_validator
from typing import Optional, List
from datetime import datetime

class CreateExamSchema(BaseModel):
    examId: Optional[str] = Field(None, min_length=2, max_length=20)
    examName: str = Field(..., min_length=2, max_length=100)
    classId: str = Field(..., min_length=1)
    academicYear: str = Field(..., min_length=4, max_length=9)
    term: str = Field(..., min_length=1, max_length=50)
    maxMarks: int = Field(100, ge=1)
    passMarks: int = Field(35, ge=0)
    startDate: str = Field(..., description="Start date format YYYY-MM-DD")
    endDate: str = Field(..., description="End date format YYYY-MM-DD")

    @field_validator("startDate", "endDate")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v

    @model_validator(mode="after")
    def check_marks_limits(self) -> 'CreateExamSchema':
        if self.passMarks > self.maxMarks:
            raise ValueError("passMarks cannot exceed maxMarks")
        # Validate startDate is before or equal to endDate
        start = datetime.strptime(self.startDate, "%Y-%m-%d")
        end = datetime.strptime(self.endDate, "%Y-%m-%d")
        if start > end:
            raise ValueError("startDate cannot be after endDate")
        return self

class UpdateExamSchema(BaseModel):
    examName: Optional[str] = Field(None, min_length=2, max_length=100)
    classId: Optional[str] = Field(None, min_length=1)
    academicYear: Optional[str] = Field(None, min_length=4, max_length=9)
    term: Optional[str] = Field(None, min_length=1, max_length=50)
    maxMarks: Optional[int] = Field(None, ge=1)
    passMarks: Optional[int] = Field(None, ge=0)
    startDate: Optional[str] = Field(None, description="Start date format YYYY-MM-DD")
    endDate: Optional[str] = Field(None, description="End date format YYYY-MM-DD")

    @field_validator("startDate", "endDate")
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v

    @model_validator(mode="after")
    def check_marks_limits(self) -> 'UpdateExamSchema':
        # If both are updated, validate
        max_m = self.maxMarks
        pass_m = self.passMarks
        if max_m is not None and pass_m is not None:
            if pass_m > max_m:
                raise ValueError("passMarks cannot exceed maxMarks")
        
        # Validate dates if both updated
        if self.startDate is not None and self.endDate is not None:
            start = datetime.strptime(self.startDate, "%Y-%m-%d")
            end = datetime.strptime(self.endDate, "%Y-%m-%d")
            if start > end:
                raise ValueError("startDate cannot be after endDate")
        return self

class BulkSubjectMarkSchema(BaseModel):
    subjectId: str = Field(...)
    marks: float = Field(..., ge=0, description="Marks scored, must be positive or zero.")

class BulkStudentMarkSchema(BaseModel):
    studentId: str = Field(...)
    subjects: List[BulkSubjectMarkSchema] = Field(..., min_length=1)

class BulkMarkEntrySchema(BaseModel):
    students: List[BulkStudentMarkSchema] = Field(..., min_length=1)

class UpdateStudentMarksSchema(BaseModel):
    subjects: List[BulkSubjectMarkSchema] = Field(..., min_length=1)
