from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database.base import Base


class Chemical(Base):
    __tablename__ = "chemicals"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    product_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )

    manufacturer: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    internal_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
        index=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Chemical → SDS ilişkisi
    sds_documents: Mapped[list["SDSDocument"]] = relationship(
        "SDSDocument",
        back_populates="chemical",
        cascade="all, delete-orphan"
    )

    # Chemical → Identifier ilişkisi
    identifiers: Mapped[list["ChemicalIdentifier"]] = relationship(
        "ChemicalIdentifier",
        back_populates="chemical",
        cascade="all, delete-orphan"
    )