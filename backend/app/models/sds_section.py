from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class SDSSection(Base):
    __tablename__ = "sds_sections"

    __table_args__ = (
        UniqueConstraint(
            "sds_document_id",
            "section_number",
            name="uq_sds_document_section"
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

    section_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    section_title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    sds_document: Mapped["SDSDocument"] = relationship(
    "SDSDocument",
    back_populates="sections"
)