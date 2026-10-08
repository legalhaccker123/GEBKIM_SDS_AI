from pathlib import Path

from app.services.pdf_reader import extract_pdf_text
from app.services.revision_parser import parse_revision_metadata


BASE_DIR = Path(__file__).resolve().parents[2]

pdf_path = (
    BASE_DIR
    / "uploads"
    / "6518b9a3dd454f819b500d7cf784306b.pdf"
)


text = extract_pdf_text(
    pdf_path
)

revision_data = parse_revision_metadata(
    text
)


print("\n")
print("=" * 70)
print("SDS REVİZYON PARSER SONUCU")
print("=" * 70)

for key, value in revision_data.items():
    print(f"{key}: {value}")