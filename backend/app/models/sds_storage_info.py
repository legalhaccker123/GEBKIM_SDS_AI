from sqlalchemy import ForeignKey, Integer, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class SDSStorageInfo(Base):
    __tablename__ = "sds_storage_info"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    sds_document_id: Mapped[int] = mapped_column(
        ForeignKey(
            "sds_documents.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        unique=True,
        index=True
    )

    # SECTION 7.1
    handling_precautions: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False
    )

    # SECTION 7.2
    storage_conditions: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False
    )

    incompatible_materials: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False
    )

    fire_explosion_precautions: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False
    )

    # SECTION 7.3
    specific_end_use: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    sds_document: Mapped["SDSDocument"] = relationship(
        "SDSDocument",
        back_populates="storage_info"
    )