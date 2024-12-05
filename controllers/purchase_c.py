from fastapi import HTTPException
from sqlmodel import Session

from database.models.purchase import (
    CreatePurchase,
    CreatePurchaseItem,
    UpdatePurchase
)
from services.purchase_s import create_purchase_db, create_purchase_item_db, delete_purchase_db, delete_purchase_item_db, get_purchase_by_id_db, get_purchases_all_db, update_purchase_db, update_purchase_item_db

def create_purchase(purchase: CreatePurchase, session: Session):
    try:
        return create_purchase_db(purchase, session)
    except Exception as e:
        return HTTPException(status_code=400, detail=str(e))

def update_purchase(purchase_id: int, purchase: UpdatePurchase, session: Session):
    try:
        return update_purchase_db(purchase, purchase_id, session)
    except Exception as e:
        return HTTPException(status_code=400, detail=str(e))

def delete_purchase(purchase_id: int, session: Session):
    try:
        return delete_purchase_db(purchase_id, session)
    except Exception as e:
        return HTTPException(status_code=400, detail=str(e))

def get_purchase_by_id(purchase_id: int, session: Session):
    try:
        return get_purchase_by_id_db(purchase_id, session)
    except Exception as e:
        return HTTPException(status_code=400, detail=str(e))

def get_purchases_all(session: Session):
    try:
        return get_purchases_all_db(session)
    except Exception as e:
        return HTTPException(status_code=400, detail=str(e))
    
    
# purchase item controller

def create_purchase_item(item: CreatePurchaseItem, session: Session):
    try:
        return create_purchase_item_db(item, session)
    except Exception as e:
        return HTTPException(status_code=400, detail=str(e))
    
def update_purchase_item(item_id: int, item: CreatePurchaseItem, session: Session):
    try:
        return update_purchase_item_db(item, item_id, session)
    except Exception as e:
        return HTTPException(status_code=400, detail=str(e))

def delete_purchase_item(item_id: int, session: Session):
    try:
        return delete_purchase_item_db(item_id, session)
    except Exception as e:
        return HTTPException(status_code=400, detail=str(e))
