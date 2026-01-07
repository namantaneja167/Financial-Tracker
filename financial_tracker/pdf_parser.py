import io
from typing import List


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract raw text from a PDF (best-effort).

    Tries `pdfplumber` first (with table extraction), then falls back to `pypdf`.
    """

    text_parts: List[str] = []

    try:
        import pdfplumber  # type: ignore

        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text_parts = []
                
                # Try to extract tables first if present
                try:
                    tables = page.extract_tables()
                    if tables:
                        # Convert tables to readable text format
                        for table in tables:
                            for row in table:
                                # Join cells with tabs for readability
                                row_text = " | ".join(str(cell or "").strip() for cell in row)
                                if row_text.strip():
                                    page_text_parts.append(row_text)
                except (AttributeError, Exception):
                    # If tables can't be extracted, skip to text extraction
                    pass
                
                # Also extract regular text
                page_text = page.extract_text() or ""
                if page_text.strip():
                    page_text_parts.append(page_text)
                
                # Add all text from this page as one block
                if page_text_parts:
                    text_parts.append("\n".join(page_text_parts))
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
