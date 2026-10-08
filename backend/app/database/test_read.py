from sqlalchemy import select

from app.database.session import SessionLocal
from app.models import Chemical


def read_chemicals():
    db = SessionLocal()

    try:
        statement = select(Chemical)
        chemicals = db.scalars(statement).all()

        print("Toplam kimyasal:", len(chemicals))

        for chemical in chemicals:
            print(
                chemical.id,
                chemical.product_name,
                chemical.manufacturer,
                chemical.internal_code
            )

    finally:
        db.close()


if __name__ == "__main__":
    read_chemicals()