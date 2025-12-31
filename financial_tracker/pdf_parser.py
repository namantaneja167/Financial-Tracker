import io
from typing import List


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract raw text from a PDF (best-effort).

    Tries `pdfplumber` first, then falls back to `pypdf`.
    """

    text_parts: List[str] = []

    try:
        import pdfplumber  # type: ignore

        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                if page_text.strip():
                    text_parts.append(page_text)
    except Exception:
        text_parts = []

    if text_parts:
        return "\n\n".join(text_parts).strip()

    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(io.BytesIO(pdf_bytes))
        for page in reader.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                text_parts.append(page_text)
    except Exception:
        pass

    return "\n\n".join(text_parts).strip()
