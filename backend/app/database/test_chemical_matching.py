from app.api.sds import find_existing_chemical
from app.database.session import SessionLocal


def main():
    db = SessionLocal()

    try:
        parsed_data = {
            # İsmi özellikle mevcut kayıttan farklı veriyoruz.
            "product_name": "Potasyum karbonat",
            "manufacturer": "Brenntag Kimya Tic. Ltd. Sti.",

            # Eşleştirmenin CAS üzerinden yapılmasını bekliyoruz.
            "cas_numbers": ["584-08-7"],

            "ec_number": "209-529-3",
            "reach_number": None,
            "product_code": None,
            "ufi": None,
        }

        chemical = find_existing_chemical(
            db=db,
            parsed_data=parsed_data
        )

        if chemical is None:
            print("Chemical eşleşmesi bulunamadı.")
            return

        print("CHEMICAL EŞLEŞMESİ BAŞARILI")
        print("-" * 50)
        print(f"Chemical ID: {chemical.id}")
        print(f"Product Name: {chemical.product_name}")
        print(f"Manufacturer: {chemical.manufacturer}")

    finally:
        db.close()


if __name__ == "__main__":
    main()