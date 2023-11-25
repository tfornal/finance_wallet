from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship
from database import Base


class Users(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    active = Column(Boolean, default=True)
    expenses = relationship("Wallet", back_populates="owner")


class Wallet(Base):
    __tablename__ = "wallet"

    id = Column(Integer, primary_key=True, index=True)
    price = Column(Float)
    description = Column(String)
    category = Column(String)
    owner_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"))

    owner = relationship("Users", back_populates="expenses")
