from pydantic import BaseModel, Field, model_validator, field_validator
from typing import Optional, List, Union
from datetime import datetime

def parse_iso_datetime(v: str) -> datetime:
    try:
        # Normalize Z to +00:00 for older Python compatibility
        if v.endswith("Z"):
            v = v[:-1] + "+00:00"
        dt = datetime.fromisoformat(v)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        raise ValueError("Datetime must be in ISO 8601 format (e.g. YYYY-MM-DDTHH:MM:SSZ)")

class QuestionSchema(BaseModel):
    questionId: Optional[str] = Field(None)
    question: str = Field(..., min_length=1)
    type: str = Field(..., description="Type of question: MCQ, TRUE_FALSE, MULTIPLE_SELECT, FILL_BLANK, SHORT_ANSWER, ESSAY")
    options: Optional[List[str]] = Field(None)
    correctAnswer: Union[str, List[str]] = Field(..., description="Correct answer(s)")
    marks: int = Field(..., gt=0)
    negativeMarks: int = Field(0, ge=0)
    explanation: Optional[str] = Field("")
    order: Optional[int] = Field(None)

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        allowed = ["MCQ", "TRUE_FALSE", "MULTIPLE_SELECT", "FILL_BLANK", "SHORT_ANSWER", "ESSAY"]
        if v not in allowed:
            raise ValueError(f"Invalid question type. Allowed: {allowed}")
        return v

    @model_validator(mode="after")
    def validate_question_details(self) -> 'QuestionSchema':
        q_type = self.type
        
        # Verify MCQ
        if q_type == "MCQ":
            if not self.options or len(self.options) < 2:
                raise ValueError("MCQ must contain at least two options.")
            # correctAnswer must be a string and in options
            if not isinstance(self.correctAnswer, str):
                raise ValueError("correctAnswer for MCQ must be a single string.")
            if self.correctAnswer not in self.options:
                raise ValueError("correctAnswer for MCQ must be one of the options.")

        # Verify TRUE_FALSE
        elif q_type == "TRUE_FALSE":
            # Force or validate options to be true/false
            if not self.options:
                self.options = ["True", "False"]
            # correctAnswer must be string
            if not isinstance(self.correctAnswer, str):
                raise ValueError("correctAnswer for TRUE_FALSE must be a single string.")
            normalized_ans = self.correctAnswer.strip().lower()
            if normalized_ans not in ["true", "false"]:
                raise ValueError("correctAnswer for TRUE_FALSE must be 'True' or 'False'.")

        # Verify MULTIPLE_SELECT
        elif q_type == "MULTIPLE_SELECT":
            if not self.options or len(self.options) < 2:
                raise ValueError("MULTIPLE_SELECT must contain at least two options.")
            
            # Correct answers parsing
            correct_list = []
            if isinstance(self.correctAnswer, list):
                correct_list = self.correctAnswer
            elif isinstance(self.correctAnswer, str):
                correct_list = [c.strip() for c in self.correctAnswer.split(",") if c.strip()]
            
            if len(correct_list) < 2:
                raise ValueError("Multiple Select questions must contain at least two correct answers.")
                
            # Verify all correct answers are in options
            for ans in correct_list:
                if ans not in self.options:
                    raise ValueError(f"Correct answer '{ans}' must be one of the options.")

        # Verify FILL_BLANK
        elif q_type == "FILL_BLANK":
            if not self.correctAnswer or (isinstance(self.correctAnswer, str) and not self.correctAnswer.strip()):
                raise ValueError("FILL_BLANK must have a correct answer.")
                
        return self

class CreateOnlineExamSchema(BaseModel):
    examId: Optional[str] = Field(None)
    title: str = Field(..., min_length=2, max_length=100)
    subjectId: str = Field(..., min_length=1)
    classIds: List[str] = Field(..., min_length=1)
    academicYear: str = Field(..., min_length=4, max_length=9)
    duration: int = Field(..., gt=0)
    passingMarks: int = Field(..., ge=0)
    startDateTime: str = Field(..., description="Start date time in ISO 8601 format")
    endDateTime: str = Field(..., description="End date time in ISO 8601 format")
    instructions: Optional[str] = Field("")
    totalMarks: Optional[int] = Field(None, ge=1)
    questions: List[QuestionSchema] = Field(..., min_length=1)

    @field_validator("startDateTime", "endDateTime")
    @classmethod
    def validate_iso_format(cls, v: str) -> str:
        parse_iso_datetime(v)
        return v

    @model_validator(mode="after")
    def validate_exam_limits(self) -> 'CreateOnlineExamSchema':
        start = parse_iso_datetime(self.startDateTime)
        end = parse_iso_datetime(self.endDateTime)
        if start >= end:
            raise ValueError("startDateTime must be before endDateTime")

        total_q_marks = sum(q.marks for q in self.questions)
        if self.totalMarks is not None:
            if self.totalMarks != total_q_marks:
                raise ValueError(f"Total exam marks ({self.totalMarks}) must equal the sum of all question marks ({total_q_marks}).")
        else:
            self.totalMarks = total_q_marks

        if self.passingMarks > self.totalMarks:
            raise ValueError("passingMarks cannot exceed totalMarks")

        return self

class UpdateOnlineExamSchema(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=100)
    subjectId: Optional[str] = Field(None, min_length=1)
    classIds: Optional[List[str]] = Field(None, min_length=1)
    academicYear: Optional[str] = Field(None, min_length=4, max_length=9)
    duration: Optional[int] = Field(None, gt=0)
    passingMarks: Optional[int] = Field(None, ge=0)
    startDateTime: Optional[str] = Field(None)
    endDateTime: Optional[str] = Field(None)
    instructions: Optional[str] = Field(None)
    totalMarks: Optional[int] = Field(None, ge=1)
    questions: Optional[List[QuestionSchema]] = Field(None)

    @field_validator("startDateTime", "endDateTime")
    @classmethod
    def validate_iso_format(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            parse_iso_datetime(v)
        return v

    @model_validator(mode="after")
    def validate_exam_limits(self) -> 'UpdateOnlineExamSchema':
        if self.startDateTime is not None and self.endDateTime is not None:
            start = parse_iso_datetime(self.startDateTime)
            end = parse_iso_datetime(self.endDateTime)
            if start >= end:
                raise ValueError("startDateTime must be before endDateTime")

        if self.questions is not None:
            total_q_marks = sum(q.marks for q in self.questions)
            if self.totalMarks is not None:
                if self.totalMarks != total_q_marks:
                    raise ValueError(f"Total exam marks ({self.totalMarks}) must equal the sum of all question marks ({total_q_marks}).")
            else:
                self.totalMarks = total_q_marks

        return self

class SaveAnswerSchema(BaseModel):
    questionId: str = Field(..., min_length=1)
    selectedAnswer: Union[str, List[str]] = Field(..., description="Selected answer(s)")

