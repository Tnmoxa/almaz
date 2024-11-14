from datetime import date

from sqlalchemy import Integer, String, Float, Date, Text
from sqlalchemy.orm import Mapped, mapped_column, MappedAsDataclass, DeclarativeBase


class Base(DeclarativeBase, MappedAsDataclass):
    pass


class SalesData(Base):
    __tablename__ = "sales_data"

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True, index=True, init=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)


class LLMAnalysisResult(Base):
    __tablename__ = "llm_analysis_result"

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True, index=True, init=False)
    date: Mapped[str] = mapped_column(Date, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
