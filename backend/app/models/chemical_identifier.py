from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ChemicalIdentifier(Base):
    __tablename__ = "chemical_identifiers"

    __table_args__ = (
        UniqueConstraint(
            "chemical_id",
            "identifier_type",
            "identifier_value",
            name="uq_chemical_identifier_per_chemical"
        ),
    )

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

    identifier_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    identifier_value: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )

    chemical: Mapped["Chemical"] = relationship(
        "Chemical",
        back_populates="identifiers"
    )