import logging
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query, status

import crud
from cache import l1
from database import get_db
from schemas import UserCreate, UserResponse, UserUpdate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserResponse])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: sqlite3.Connection = Depends(get_db),
):
    return crud.get_users(db, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: sqlite3.Connection = Depends(get_db)):
    cached = l1.get(f"user:{user_id}")
    if cached is not None:
        return cached
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    l1.set(f"user:{user_id}", user)
    return user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(data: UserCreate, db: sqlite3.Connection = Depends(get_db)):
    if crud.get_user_by_email(db, data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )
    logger.info("Creating user email=%s", data.email)
    try:
        user = crud.create_user(db, data)
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        ) from None
    l1.set(f"user:{user['id']}", user)
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int, data: UserUpdate, db: sqlite3.Connection = Depends(get_db)
):
    try:
        user = crud.update_user(db, user_id, data)
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        ) from None
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    l1.set(f"user:{user_id}", user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: sqlite3.Connection = Depends(get_db)):
    if not crud.delete_user(db, user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    l1.delete(f"user:{user_id}")
    l1.invalidate_prefix("item:")
    logger.info("Deleted user id=%d", user_id)
