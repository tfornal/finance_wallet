from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
    ForeignKey,
    Float,
    Date,
    func,
)
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
    assets = relationship("Assets", back_populates="owner")


class Wallet(Base):
    __tablename__ = "wallet"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    price = Column(Float)
    category = Column(String)
    date = Column(Date, server_default=func.date(), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"))

    owner = relationship("Users", back_populates="expenses")


class Assets(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    asset_value_pln = Column(Float)
    percentage_share = Column(Float)
    category = Column(String)
    owner_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"))

    owner = relationship("Users", back_populates="assets")
