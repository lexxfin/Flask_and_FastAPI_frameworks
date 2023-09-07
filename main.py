import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from databases import Database
from datetime import datetime

DATABASE_URL = "sqlite:///./main.db"
database = Database(DATABASE_URL)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

app = FastAPI()


class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int


class ProductBase(BaseModel):
    name: str
    description: str
    price: float


class ProductCreate(ProductBase):
    pass


class Product(ProductBase):
    id: int


class OrderBase(BaseModel):
    user_id: int
    product_id: int


class OrderCreate(OrderBase):
    pass


class Order(OrderBase):
    id: int
    order_date: datetime
    status: str


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    orders = relationship("OrderModel", back_populates="user")


class ProductModel(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    price = Column(Float)
    orders = relationship("OrderModel", back_populates="product")


class OrderModel(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    order_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="Pending")

    user = relationship("UserModel", back_populates="orders")
    product = relationship("ProductModel", back_populates="orders")


Base.metadata.create_all(bind=engine)


@app.post("/users/", response_model=User)
async def create_user(user: UserCreate):
    async with database.transaction():
        query = UserModel.__table__.insert().values(**user.dict(), password=user.password)
        last_record_id = await database.execute(query)
        user.id = last_record_id
        return user


@app.get("/users/{user_id}", response_model=User)
async def read_user(user_id: int):
    query = UserModel.__table__.select().where(UserModel.id == user_id)
    user = await database.fetch_one(query)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.post("/products/", response_model=Product)
async def create_product(product: ProductCreate):
    async with database.transaction():
        query = ProductModel.__table__.insert().values(**product.dict())
        last_record_id = await database.execute(query)
        product.id = last_record_id
        return product


@app.get("/products/{product_id}", response_model=Product)
async def read_product(product_id: int):
    query = ProductModel.__table__.select().where(ProductModel.id == product_id)
    product = await database.fetch_one(query)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.post("/orders/", response_model=Order)
async def create_order(order: OrderCreate):
    async with database.transaction():
        query = OrderModel.__table__.insert().values(**order.dict(), order_date=datetime.utcnow())
        last_record_id = await database.execute(query)
        order.id = last_record_id
        order.order_date = datetime.utcnow()
        order.status = "Pending"
        return order


@app.get("/orders/{order_id}", response_model=Order)
async def read_order(order_id: int):
    query = OrderModel.__table__.select().where(OrderModel.id == order_id)
    order = await database.fetch_one(query)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.put("/orders/{order_id}", response_model=Order)
async def update_order(order_id: int, updated_order: OrderCreate):
    async with database.transaction():
        query = OrderModel.__table__.update().where(OrderModel.id == order_id).values(**updated_order.dict())
        await database.execute(query)
        updated_order.id = order_id
        return updated_order


@app.delete("/orders/{order_id}", response_model=Order)
async def delete_order(order_id: int):
    query = OrderModel.__table__.delete().where(OrderModel.id == order_id)
    deleted_order = await database.execute(query)
    if deleted_order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return deleted_order


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
