from datetime import datetime
from pydantic import BaseModel


# --- User ---

class UserBase(BaseModel):
    name: str
    email: str


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    is_active: bool | None = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Item ---

class ItemBase(BaseModel):
    title: str
    description: str | None = None


class ItemCreate(ItemBase):
    owner_id: int


class ItemUpdate(BaseModel):
    title: str | None = None
    description: str | None = None


class ItemResponse(ItemBase):
    id: int
    owner_id: int

    model_config = {"from_attributes": True}
