from datetime import datetime
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class MSME(Base):
    __tablename__ = "msmes"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_name: Mapped[str] = mapped_column(String(160), unique=True)
    industry: Mapped[str] = mapped_column(String(80))
    business_age: Mapped[float] = mapped_column(Float)
    location: Mapped[str] = mapped_column(String(100), default="India")
    employees: Mapped[int] = mapped_column(Integer, default=1)
    ownership_type: Mapped[str] = mapped_column(String(60), default="Private Limited")
    business_type: Mapped[str] = mapped_column(String(60), default="B2B")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    assessments: Mapped[list["Assessment"]] = relationship(back_populates="msme", cascade="all, delete-orphan")

class User(Base):
    """Local demo user; suitable for a college prototype, not enterprise identity."""
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    role: Mapped[str] = mapped_column(String(60), default="Credit Analyst")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Assessment(Base):
    __tablename__ = "assessments"
    id: Mapped[int] = mapped_column(primary_key=True)
    msme_id: Mapped[int] = mapped_column(ForeignKey("msmes.id"))
    payload: Mapped[dict] = mapped_column(JSON)
    result: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    msme: Mapped[MSME] = relationship(back_populates="assessments")

