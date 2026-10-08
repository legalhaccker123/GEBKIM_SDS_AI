from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class HazardStatement(Base):
    __tablename__ = "hazard_statements"

    __table_args__ = (
        UniqueConstraint(
            "sds_document_id",
            "code",
            name="uq_sds_hazard_code"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    sds_document_id: Mapped[int] = mapped_column(
        ForeignKey("sds_documents.id"),
        nullable=False,
        index=True
    )

    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True
    )

    statement_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    sds_document: Mapped["SDSDocument"] = relationship(
        "SDSDocument",
        back_populates="hazard_statements"
    )


class PrecautionaryStatement(Base):
    __tablename__ = "precautionary_statements"

    __table_args__ = (
        UniqueConstraint(
            "sds_document_id",
            "code",
            name="uq_sds_precautionary_code"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    sds_document_id: Mapped[int] = mapped_column(
        ForeignKey("sds_documents.id"),
        nullable=False,
        index=True
    )

    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    statement_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    sds_document: Mapped["SDSDocument"] = relationship(
        "SDSDocument",
        back_populates="precautionary_statements"
    )


class GHSPictogram(Base):
    __tablename__ = "ghs_pictograms"

    __table_args__ = (
        UniqueConstraint(
            "sds_document_id",
            "code",
            name="uq_sds_ghs_code"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    sds_document_id: Mapped[int] = mapped_column(
        ForeignKey("sds_documents.id"),
        nullable=False,
        index=True
    )

    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True
    )

    sds_document: Mapped["SDSDocument"] = relationship(
        "SDSDocument",
        back_populates="ghs_pictograms"
    )