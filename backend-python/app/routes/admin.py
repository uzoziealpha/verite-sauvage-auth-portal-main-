from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from .. import schemas, crud

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/products", response_model=schemas.ProductOut, status_code=status.HTTP_201_CREATED)
def register_product(product_in: schemas.ProductCreate, db: Session = Depends(get_db)):
    existing = crud.get_product_by_code(db, product_in.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product with this code already exists.",
        )

    return crud.create_product(db, product_in)


@router.get("/products/{code}", response_model=schemas.ProductOut)
def get_product(code: str, db: Session = Depends(get_db)):
    product = crud.get_product_by_code(db, code)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.patch("/products/{code}", response_model=schemas.ProductOut)
def update_product(code: str, product_update: schemas.ProductUpdate, db: Session = Depends(get_db)):
    product = crud.get_product_by_code(db, code)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return crud.update_product(db, product_update)
