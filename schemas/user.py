from pydantic import BaseModel, field_validator


class SignupSchema(BaseModel):
    name: str
    phone: str
    password: str
    role: str = "customer"

    @field_validator("password")
    def password_length(cls, v):
        if len(v) > 72:
            raise ValueError("Password too long, max 72 characters")
        if len(v) < 6:
            raise ValueError("Password too short, min 6 characters")
        return v


class LoginSchema(BaseModel):
    phone: str
    password: str
