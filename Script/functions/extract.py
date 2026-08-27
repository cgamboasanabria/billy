"""Text extraction from source PDFs (and optional OCR).

Used to build an additional grounded corpus for the tutor from the official
textbooks. PDF text extraction uses pypdf; OCR is optional and only runs when
pytesseract plus a Tesseract binary are available.
"""

from __future__ import annotations

from pathlib import Path


def extract_pdf_text(pdf_path: str | Path) -> str:
    """Extract text from a PDF using pypdf."""
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    parts: list[str] = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n".join(parts).strip()


def ocr_image(image_path: str | Path) -> str:
    """Return OCR text for an image, or empty if Tesseract is unavailable."""
    try:
        import pytesseract  # type: ignore
        from PIL import Image

        return pytesseract.image_to_string(Image.open(str(image_path)))
    except Exception:
        return ""
