import re
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import SDSDocument


def _version_to_tuple(
    version: str | None
) -> tuple[int, ...] | None:
    """
    Version bilgisini karşılaştırılabilir tuple'a çevirir.

    Örnek:
    "1.0" -> (1, 0)
    "2.1" -> (2, 1)
    "3"   -> (3,)
    """

    if not version:
        return None

    numbers = re.findall(
        r"\d+",
        version
    )

    if not numbers:
        return None

    return tuple(
        int(number)
        for number in numbers
    )


def _effective_date(
    revision_date: date | None,
    preparation_date: date | None
) -> date | None:
    """
    SDS karşılaştırmasında kullanılacak tarihi belirler.

    Öncelik:
    1. Revision Date
    2. Preparation Date
    """

    if revision_date is not None:
        return revision_date

    return preparation_date


def determine_is_current(
    db: Session,
    chemical_id: int,
    new_revision_date: date | None,
    new_preparation_date: date | None,
    new_version: str | None
) -> bool:
    """
    Yeni SDS'nin current olup olmayacağını belirler.

    Tarih karşılaştırmasında:

    1. revision_date varsa revision_date kullanılır.
    2. revision_date yoksa preparation_date kullanılır.
    3. Tarihler aynıysa version karşılaştırılır.
    4. Güvenilir karşılaştırma yapılamıyorsa mevcut
       current SDS değiştirilmez.

    Bu fonksiyon commit yapmaz.
    """

    statement = (
        select(SDSDocument)
        .where(
            SDSDocument.chemical_id == chemical_id,
            SDSDocument.is_current.is_(True)
        )
        .order_by(
            SDSDocument.uploaded_at.desc()
        )
    )

    current_documents = db.scalars(
        statement
    ).all()

    # -------------------------------------------------
    # CURRENT SDS YOK
    # -------------------------------------------------

    if not current_documents:
        return True

    current_sds = current_documents[0]

    # -------------------------------------------------
    # EFFECTIVE DATE
    # -------------------------------------------------

    new_effective_date = _effective_date(
        revision_date=new_revision_date,
        preparation_date=new_preparation_date
    )

    current_effective_date = _effective_date(
        revision_date=current_sds.revision_date,
        preparation_date=current_sds.preparation_date
    )

    # -------------------------------------------------
    # İKİ TARİH DE VARSA KARŞILAŞTIR
    # -------------------------------------------------

    if (
        new_effective_date is not None
        and current_effective_date is not None
    ):

        # Yeni SDS daha yeni
        if new_effective_date > current_effective_date:

            for document in current_documents:
                document.is_current = False

            return True

        # Yeni SDS daha eski
        if new_effective_date < current_effective_date:
            return False

        # -------------------------------------------------
        # TARİHLER AYNI → VERSION KARŞILAŞTIR
        # -------------------------------------------------

        new_version_tuple = _version_to_tuple(
            new_version
        )

        current_version_tuple = _version_to_tuple(
            current_sds.version
        )

        if (
            new_version_tuple is not None
            and current_version_tuple is not None
            and new_version_tuple > current_version_tuple
        ):

            for document in current_documents:
                document.is_current = False

            return True

        return False

    # -------------------------------------------------
    # TARİHLER KARŞILAŞTIRILAMIYOR
    # -------------------------------------------------

    return False