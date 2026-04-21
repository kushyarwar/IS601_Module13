from pydantic import BaseModel, EmailStr, Field, model_validator
from datetime import datetime
from typing import Optional

from app.calculator import OperationType


# ── User schemas ───────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: Optional[str] = None
    email: EmailStr
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: int
    username: str
    email: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class RegisterResponse(BaseModel):
    token: str
    message: str
    user: UserRead


class LoginResponse(BaseModel):
    token: str
    message: str
    user: UserRead


# ── Calculation schemas ────────────────────────────────────────────────────

class CalculationCreate(BaseModel):
    a: float
    b: float
    type: OperationType
    user_id: int

    @model_validator(mode="after")
    def check_divide_by_zero(self):
        if self.type == OperationType.Divide and self.b == 0:
            raise ValueError("Division by zero is not allowed")
        return self


class CalculationUpdate(BaseModel):
    a: Optional[float] = None
    b: Optional[float] = None
    type: Optional[OperationType] = None

    @model_validator(mode="after")
    def check_divide_by_zero(self):
        if self.type == OperationType.Divide and self.b == 0:
            raise ValueError("Division by zero is not allowed")
        return self


class CalculationRead(BaseModel):
    id: int
    a: float
    b: float
    type: OperationType
    result: float
    timestamp: Optional[datetime] = None
    user_id: int

    model_config = {"from_attributes": True}


class CalculationWithUser(BaseModel):
    username: str
    a: float
    b: float
    type: str
    result: float
