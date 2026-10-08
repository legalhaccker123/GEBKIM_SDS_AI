from pathlib import Path

from app.services.pdf_reader import extract_pdf_text
from app.services.document_classifier import classify_document
from app.services.section_splitter import split_sds_sections


BASE_DIR = Path(__file__).resolve().parents[2]

pdf_path = (
    BASE_DIR
    / "uploads"
    / "c766e449ed3945fbb58a597672e26c61.pdf"
)

print("PDF:", pdf_path)
print("Dosya var mı?:", pdf_path.exists())

# PDF metnini çıkar
text = extract_pdf_text(pdf_path)

# Doküman tipini belirle
document_type = classify_document(text)

print("Doküman tipi:", document_type)
print("Karakter sayısı:", len(text))

# SDS ise bölümlere ayır
if document_type == "SDS":

    sections = split_sds_sections(text)

    print("Bulunan bölüm sayısı:", len(sections))
    print("Bulunan bölümler:", sorted(sections.keys()))

    for section_number in sorted(sections.keys()):
        content = sections[section_number]

        print()
        print("=" * 60)
        print(f"BÖLÜM {section_number}")
        print("=" * 60)

        # Terminali çok doldurmamak için
        # her bölümün ilk 300 karakterini göster
        print(content[:300])

else:
    print("Bu doküman SDS olarak sınıflandırılmadı.")