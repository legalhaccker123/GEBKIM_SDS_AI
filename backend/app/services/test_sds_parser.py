from pathlib import Path

from app.services.pdf_reader import extract_pdf_text
from app.services.section_splitter import split_sds_sections
from app.services.sds_parser import parse_section_1


BASE_DIR = Path(__file__).resolve().parents[2]

pdf_path = (
    BASE_DIR
    / "uploads"
    / "6518b9a3dd454f819b500d7cf784306b.pdf"
)

text = extract_pdf_text(pdf_path)

sections = split_sds_sections(text)

section_1 = sections.get(1)

if section_1 is None:
    print("BÖLÜM 1 bulunamadı.")

else:
    print("\n")
    print("=" * 70)
    print("PDF'DEN ÇIKARILAN HAM BÖLÜM 1")
    print("=" * 70)
    print(section_1)

    print("\n")
    print("=" * 70)
    print("BÖLÜM 1 PARSER SONUCU")
    print("=" * 70)

    parsed_data = parse_section_1(section_1)

    for key, value in parsed_data.items():
        print(f"{key}: {value}")