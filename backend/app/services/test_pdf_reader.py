from pathlib import Path

from app.services.pdf_reader import extract_pdf_text


pdf_path = Path(
    r"uploads\69bb142bd9c74aa6802cff5b716a47a3.pdf"
)

print("PDF yolu:", pdf_path)
print("Dosya var mı?:", pdf_path.exists())

text = extract_pdf_text(pdf_path)

print(text[:2000])
print("\nKarakter sayısı:", len(text))