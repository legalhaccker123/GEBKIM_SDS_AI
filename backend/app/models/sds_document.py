from datetime import date

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database.base import Base


class SDSDocument(Base):
    __tablename__ = "sds_documents"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    chemical_id: Mapped[int] = mapped_column(
        ForeignKey("chemicals.id"),
        nullable=False,
        index=True
    )

    original_filename: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    stored_filename: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    file_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True
    )

    preparation_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    revision_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    language: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    is_current: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    processing_status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False
    )

    uploaded_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    # =====================================================
    # RELATIONSHIPS
    # =====================================================

    chemical: Mapped["Chemical"] = relationship(
        "Chemical",
        back_populates="sds_documents"
    )

    sections: Mapped[list["SDSSection"]] = relationship(
        "SDSSection",
        back_populates="sds_document",
        cascade="all, delete-orphan"
    )

    hazard_statements: Mapped[list["HazardStatement"]] = relationship(
        "HazardStatement",
        back_populates="sds_document",
        cascade="all, delete-orphan"
    )

    precautionary_statements: Mapped[
        list["PrecautionaryStatement"]
    ] = relationship(
        "PrecautionaryStatement",
        back_populates="sds_document",
        cascade="all, delete-orphan"
    )

    ghs_pictograms: Mapped[list["GHSPictogram"]] = relationship(
        "GHSPictogram",
        back_populates="sds_document",
        cascade="all, delete-orphan"
    )

    # =====================================================
    # SECTION 7
    # =====================================================

    storage_info: Mapped["SDSStorageInfo"] = relationship(
        "SDSStorageInfo",
        back_populates="sds_document",
        cascade="all, delete-orphan",
        uselist=False
    )

    # =====================================================
    # SECTION 8
    # =====================================================

    ppe_info: Mapped["SDSPPEInfo"] = relationship(
        "SDSPPEInfo",
        back_populates="sds_document",
        cascade="all, delete-orphan",
        uselist=False
    )

    # =====================================================
    # SECTION 9
    # =====================================================

    physical_properties: Mapped[
        "SDSPhysicalProperties"
    ] = relationship(
        "SDSPhysicalProperties",
        back_populates="sds_document",
        cascade="all, delete-orphan",
        uselist=False
    )