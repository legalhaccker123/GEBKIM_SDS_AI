from app.database.session import SessionLocal
from app.models import Chemical


def create_test_chemical():
    db = SessionLocal()

    try:
        chemical = Chemical(
            product_name="Test Chemical",
            manufacturer="GEBKIM Test",
            description="Development test record",
            internal_code="TEST-001"
        )

        db.add(chemical)
        db.commit()
        db.refresh(chemical)

        print("Kimyasal başarıyla kaydedildi.")
        print("ID:", chemical.id)
        print("Ürün adı:", chemical.product_name)

    finally:
        db.close()


if __name__ == "__main__":
    create_test_chemical()