from sqlalchemy import select

from app.database.session import SessionLocal
from app.models import Chemical, ChemicalIdentifier


def main():
    db = SessionLocal()

    try:
        # Potassium carbonate kaydını bul
        chemical = db.scalar(
            select(Chemical).where(
                Chemical.product_name == "Potassium carbonate"
            )
        )

        if chemical is None:
            print("Potassium carbonate bulunamadı.")
            return

        print(
            f"Chemical bulundu: "
            f"ID={chemical.id}, "
            f"Ürün={chemical.product_name}"
        )

        identifiers_to_add = [
            ("CAS", "584-08-7"),
            ("EC", "209-529-3"),
        ]

        for identifier_type, identifier_value in identifiers_to_add:

            # Aynı identifier daha önce kaydedilmiş mi?
            existing_identifier = db.scalar(
                select(ChemicalIdentifier).where(
                    ChemicalIdentifier.identifier_type == identifier_type,
                    ChemicalIdentifier.identifier_value == identifier_value
                )
            )

            if existing_identifier:
                print(
                    f"{identifier_type} zaten kayıtlı: "
                    f"{identifier_value}"
                )
                continue

            identifier = ChemicalIdentifier(
                chemical_id=chemical.id,
                identifier_type=identifier_type,
                identifier_value=identifier_value
            )

            db.add(identifier)

            print(
                f"{identifier_type} eklendi: "
                f"{identifier_value}"
            )

        db.commit()

        print("\nKayıt tamamlandı.")

        # Sonucu tekrar veritabanından oku
        identifiers = db.scalars(
            select(ChemicalIdentifier)
            .where(
                ChemicalIdentifier.chemical_id == chemical.id
            )
            .order_by(
                ChemicalIdentifier.identifier_type
            )
        ).all()

        print("\nCHEMICAL IDENTIFIERS")
        print("-" * 50)

        for identifier in identifiers:
            print(
                f"{identifier.identifier_type}: "
                f"{identifier.identifier_value}"
            )

    finally:
        db.close()


if __name__ == "__main__":
    main()