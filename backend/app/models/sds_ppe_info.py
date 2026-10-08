from sqlalchemy import ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class SDSPPEInfo(Base):
    __tablename__ = "sds_ppe_info"

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

    respiratory_protection: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False
    )

    hand_protection: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False
    )

    glove_materials: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False
    )

    glove_thickness: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False
    )

    eye_face_protection: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False
    )

    body_protection: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False
    )

    engineering_controls: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False
    )

    exposure_limits: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False
    )

    dnel: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False
    )

    pnec: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False
    )

    hygiene_measures: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False
    )

    sds_document: Mapped["SDSDocument"] = relationship(
        "SDSDocument",
        back_populates="ppe_info"
    )