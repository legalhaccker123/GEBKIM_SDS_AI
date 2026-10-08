from pathlib import Path

from app.services.document_classifier import classify_document
from app.services.pdf_reader import extract_pdf_text


BASE_DIR = Path(__file__).resolve().parents[2]

pdf_path = (
    BASE_DIR
    / "uploads"
    / "69bb142bd9c74aa6802cff5b716a47a3.pdf"
)

text = extract_pdf_text(pdf_path)

document_type = classify_document(text)

print("Doküman tipi:", document_type)
print("Karakter sayısı:", len(text))