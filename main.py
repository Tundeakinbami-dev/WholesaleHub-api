from fastapi import FastAPI, HTTPException

from pydantic import BaseModel

app = FastAPI()

class ProductCreate(BaseModel):
    name: str
    stock: int
    size: str

products = [
    {"id": 1, "name": "Rice", "stock": 50, "size": "5 kg"},
    {"id": 2, "name": "Cooking Oil", "stock": 30, "size": "1 litre"},
]

def get_products():
    return products

@app.get("/products")
def products_route():
    return get_products()

@app.post("/products")
def create_product(product: ProductCreate):
    product_data = product.model_dump() #pydantic provides this method
    for product in products:
            if (product["name"].strip().lower() 
                == product_data["name"].strip().lower() 
                and product["size"].strip().lower() 
                == product_data["size"].strip().lower()) : 
                raise HTTPException(
                    status_code=409,
                    detail="Product already exists"
                )
    next_id = max(product["id"] for product in products) + 1
    product_data["id"] = next_id
    products.append(product_data)
    print("Current Products:", products)
    
    return product_data

def get_product(product_id: int):
    for product in products:
        if product["id"] == product_id:
            return product

    raise HTTPException(
        status_code=404,
        detail="product not found"
    )

@app.get("/products/{product_id}") #this returns the procuct when fastAPI receives a GET request to /.products 
def product_route(product_id: int):
    return get_product(product_id)

