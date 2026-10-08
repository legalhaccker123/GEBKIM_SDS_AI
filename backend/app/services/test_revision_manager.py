from datetime import date

from app.database.session import SessionLocal
from app.services.revision_manager import determine_is_current


def main():

    db = SessionLocal()

    try:

        # Supma MA/AA (48%)
        # Chemical ID = 7
        #
        # Mevcut SDS:
        # revision_date = 2019-10-25

        chemical_id = 7

        print("\n" + "=" * 70)
        print("REVISION MANAGER TEST")
        print("=" * 70)

        # -------------------------------------------------
        # TEST 1 - DAHA ESKİ SDS
        # -------------------------------------------------

        result_old = determine_is_current(
            db=db,
            chemical_id=chemical_id,
            new_revision_date=date(2018, 1, 1)
        )

        print()
        print("TEST 1 - Eski SDS")
        print("Yeni tarih: 2018-01-01")
        print(f"is_current sonucu: {result_old}")

        # Test sırasında yapılan değişiklikleri geri al
        db.rollback()

        # -------------------------------------------------
        # TEST 2 - DAHA YENİ SDS
        # -------------------------------------------------

        result_new = determine_is_current(
            db=db,
            chemical_id=chemical_id,
            new_revision_date=date(2025, 1, 1)
        )

        print()
        print("TEST 2 - Yeni SDS")
        print("Yeni tarih: 2025-01-01")
        print(f"is_current sonucu: {result_new}")

        # Gerçek veritabanını değiştirmiyoruz.
        db.rollback()

        # -------------------------------------------------
        # TEST 3 - TARİH YOK
        # -------------------------------------------------

        result_missing = determine_is_current(
            db=db,
            chemical_id=chemical_id,
            new_revision_date=None
        )

        print()
        print("TEST 3 - Revision tarihi yok")
        print("Yeni tarih: None")
        print(f"is_current sonucu: {result_missing}")

        db.rollback()

    finally:

        db.close()


if __name__ == "__main__":
    main()
