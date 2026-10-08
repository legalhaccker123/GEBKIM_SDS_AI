from app.database.base import Base
from app.database.session import engine

# Modelleri Base metadata'ya kaydetmek için import ediyoruz.
from app.models import Chemical, SDSDocument, SDSSection


def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Veritabanı tabloları oluşturuldu.")