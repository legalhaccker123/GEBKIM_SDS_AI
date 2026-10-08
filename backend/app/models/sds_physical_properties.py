from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class SDSPhysicalProperties(Base):
    __tablename__ = "sds_physical_properties"

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

    physical_state: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    color: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    odor: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    ph: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    flash_point: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    boiling_point: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    melting_freezing_point: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    density: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    viscosity: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    solubility: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    vapour_pressure: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    flammability: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    explosive_properties: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    oxidising_properties: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    lower_explosion_limit: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    upper_explosion_limit: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    sds_document: Mapped["SDSDocument"] = relationship(
        "SDSDocument",
        back_populates="physical_properties"
    )