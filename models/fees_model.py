from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime

class FeeItemSchema(BaseModel):
    name: str = Field(..., min_length=1, description="Name of the fee item.")
    amount: float = Field(..., ge=0, description="Amount of the fee item. Must not be negative.")

class CreateFeeStructureSchema(BaseModel):
    title: str = Field(..., min_length=1, description="Title of the fee structure.")
    academicYear: str = Field(..., min_length=1, description="Academic year (e.g. 2026-2027).")
    classIds: List[str] = Field(..., min_items=1, description="List of class IDs assigned.")
    feeItems: List[FeeItemSchema] = Field(..., min_items=1, description="List of fee items.")
    dueDate: str = Field(..., min_length=1, description="Due date in YYYY-MM-DD format.")

    @field_validator('dueDate')
    @classmethod
    def validate_due_date(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Due date must be in YYYY-MM-DD format.")
        return v

class UpdateFeeStructureSchema(BaseModel):
    title: str = Field(..., min_length=1, description="Title of the fee structure.")
    academicYear: str = Field(..., min_length=1, description="Academic year (e.g. 2026-2027).")
    classIds: List[str] = Field(..., min_items=1, description="List of class IDs assigned.")
    feeItems: List[FeeItemSchema] = Field(..., min_items=1, description="List of fee items.")
    dueDate: str = Field(..., min_length=1, description="Due date in YYYY-MM-DD format.")

    @field_validator('dueDate')
    @classmethod
    def validate_due_date(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Due date must be in YYYY-MM-DD format.")
        return v

class RecordPaymentSchema(BaseModel):
    studentId: str = Field(..., min_length=1, description="Student ID.")
    feeStructureId: str = Field(..., min_length=1, description="Fee Structure ID.")
    amount: float = Field(..., gt=0, description="Payment amount. Must be positive.")
    paymentMode: str = Field(..., min_length=1, description="Payment mode (e.g. Cash, Card, Online).")
    transactionId: str = Field(..., min_length=1, description="Transaction ID.")

class SendReminderSchema(BaseModel):
    studentIds: List[str] = Field(..., min_items=1, description="List of student IDs.")
    message: str = Field(..., min_length=1, description="Reminder message.")
