from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# --- User ---


class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    email: EmailStr


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    email: EmailStr | None = None
    is_active: bool | None = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


# --- Item ---


class ItemBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    description: str | None = None


class ItemCreate(ItemBase):
    owner_id: int


class ItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=256)
    description: str | None = None


class ItemResponse(ItemBase):
    id: int
    owner_id: int
    model_config = {"from_attributes": True}
