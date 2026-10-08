from pathlib import Path

from pypdf import PdfReader


def extract_pdf_text(file_path: Path) -> str:
    reader = PdfReader(str(file_path))

    pages_text = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""

        pages_text.append(
            f"\n--- PAGE {page_number} ---\n{text.strip()}"
        )

    return "\n".join(pages_text).strip()