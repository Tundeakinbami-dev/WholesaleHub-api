from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from database import SessionLocal
from models import Product, Sale

app = FastAPI()

class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    stock: int = Field(ge=0)
    size: str = Field(min_length=1, max_length=50)
    price: int = Field(ge=0)

    @field_validator("name", "size", mode="before")
    @classmethod
    def strip_whitespace(cls, value):
        if isinstance(value, str):
            value = value.strip()
        return value

class ProductUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    stock: int = Field(ge=0)
    size: str = Field(min_length=1, max_length=50)

    @field_validator("name", "size", mode="before")
    @classmethod
    def strip_whitespace(cls, value):
        if isinstance(value, str):
            value = value.strip()
        return value

class SaleRequest(BaseModel):
    quantity: int = Field(ge=0)

products = [
    {"id": 1, "name": "Rice", "stock": 50, "size": "5 kg"},
    {"id": 2, "name": "Cooking Oil", "stock": 30, "size": "1 litre"},
]

def get_products():
    db = SessionLocal()
    try:
        return db.query(Product).all()
    finally:
        db.close()


@app.get("/products")
def products_route():
    return get_products()



@app.post("/products", status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate):
    db = SessionLocal()

    try:
        product_name = product.name.strip()
        product_size = product.size.strip()

        existing_product = db.query(Product).filter(
            Product.name.ilike(product_name),
            Product.size.ilike(product_size)
        ).first()

        if existing_product:
            raise HTTPException(
                status_code=409,
                detail="Product already exists"
            )

        new_product = Product(
            name=product_name,
            stock=product.stock,
            size=product_size,
            price=product.price
        )

        db.add(new_product)
        db.commit()
        db.refresh(new_product)

        return {
            "id": new_product.id,
            "name": new_product.name,
            "stock": new_product.stock,
            "size": new_product.size,
            "price": new_product.price
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def get_product(product_id: int):
    db = SessionLocal()

    try:
        product = db.query(Product).filter(
            Product.id == product_id
        ).first()

        if product is None:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        return {
            "id": product.id,
            "name": product.name,
            "stock": product.stock,
            "size": product.size,
            "price": product.price
        }

    finally:
        db.close()

@app.get("/products/{product_id}") #this returns the procuct when fastAPI receives a GET request to /.products 
def product_route(product_id: int):
    return get_product(product_id)

@app.put("/products/{product_id}")
def update_product(product_id: int, product_data: ProductUpdate):
    db = SessionLocal()

    try:
        product = db.query(Product).filter(
            Product.id == product_id
        ).first()

        if product is None:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        product.name = product_data.name
        product.stock = product_data.stock
        product.size = product_data.size

        db.commit()
        db.refresh(product)

        return {
            "id": product.id,
            "name": product.name,
            "stock": product.stock,
            "size": product.size
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()



@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    db = SessionLocal()

    try:
        product = db.query(Product).filter(
            Product.id == product_id
        ).first()

        if product is None:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        db.delete(product)
        db.commit()

        return {
            "message": "Product deleted successfully",
            "id": product_id
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


@app.post("/products/{product_id}/sell")
def sell_product(product_id: int, sale: SaleRequest):
    db = SessionLocal()

    try:
        product = db.query(Product).filter(
            Product.id == product_id
        ).first()

        if product is None:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        if product.stock < sale.quantity:
            raise HTTPException(
                status_code=400,
                detail="Insufficient stock"
            )

        # Reduce the available stock
        product.stock -= sale.quantity

        # Create a permanent sales record
        sale_record = Sale(
            product_id=product.id,
            quantity=sale.quantity
        )

        db.add(sale_record)

        # Save both changes together
        db.commit()

        db.refresh(product)
        db.refresh(sale_record)

        return {
            "message": "Sale completed successfully",
            "product_id": product.id,
            "name": product.name,
            "quantity_sold": sale_record.quantity,
            "remaining_stock": product.stock,
            "sale_id": sale_record.id,
            "sold_at": sale_record.sold_at
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


@app.get("/sales")
def get_sales():
    db = SessionLocal()

    try:
        sales = db.query(Sale).order_by(Sale.id.desc()).all()

        return [
            {
                "sale_id": sale.id,
                "product_id": sale.product_id,
                "quantity_sold": sale.quantity,
                "sold_at": sale.sold_at
            }
            for sale in sales
        ]

    finally:
        db.close()


