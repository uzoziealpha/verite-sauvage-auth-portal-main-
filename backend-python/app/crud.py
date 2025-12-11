from sqlalchemy.orm import Session
from . import models, schemas


def get_product_by_code(db: Session, code: str):
    return db.query(models.Product).filter(models.Product.code == code).first()


def create_product(db: Session, product_in: schemas.ProductCreate):
    product = models.Product(
        code=product_in.code,
        name=product_in.name,
        collection=product_in.collection,
        serial=product_in.serial,
        description=product_in.description,
        image_url=str(product_in.image_url) if product_in.image_url else None,
        authentic=product_in.authentic,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(db: Session, product: models.Product, product_update: schemas.ProductUpdate):
    data = product_update.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product
