from pydantic import BaseModel, Field

class UserLoginSchema(BaseModel):
    userId: str = Field(..., min_length=3, max_length=50, description="Unique identifier for the user login.")
    password: str = Field(..., min_length=6, description="User password.")

class ChangePasswordSchema(BaseModel):
    oldPassword: str = Field(..., min_length=6)
    newPassword: str = Field(..., min_length=6)

class ResetPasswordSchema(BaseModel):
    newPassword: str = Field(..., min_length=6)
