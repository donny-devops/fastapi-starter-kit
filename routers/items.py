import logging
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query, status

import crud
from cache import l1
from database import get_db
from schemas import ItemCreate, ItemResponse, ItemUpdate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/items", tags=["items"])


@router.get("/", response_model=list[ItemResponse])
def list_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: sqlite3.Connection = Depends(get_db),
):
    return crud.get_items(db, skip=skip, limit=limit)


@router.get("/{item_id}", response_model=ItemResponse)
def get_item(item_id: int, db: sqlite3.Connection = Depends(get_db)):
    cached = l1.get(f"item:{item_id}")
    if cached is not None:
        return cached
    item = crud.get_item(db, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )
    l1.set(f"item:{item_id}", item)
    return item


@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(data: ItemCreate, db: sqlite3.Connection = Depends(get_db)):
    if not crud.get_user(db, data.owner_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Owner user not found"
        )
    logger.info("Creating item title=%s owner_id=%d", data.title, data.owner_id)
    item = crud.create_item(db, data)
    l1.set(f"item:{item['id']}", item)
    return item


@router.put("/{item_id}", response_model=ItemResponse)
def update_item(
    item_id: int, data: ItemUpdate, db: sqlite3.Connection = Depends(get_db)
):
    item = crud.update_item(db, item_id, data)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )
    l1.set(f"item:{item_id}", item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: sqlite3.Connection = Depends(get_db)):
    if not crud.delete_item(db, item_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )
    l1.delete(f"item:{item_id}")
    logger.info("Deleted item id=%d", item_id)
