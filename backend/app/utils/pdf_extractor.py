from io import BytesIO

from pypdf import PdfReader

from app.core.exceptions import BadRequestError


def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(file_bytes))
    except Exception as exc:
        raise BadRequestError("Invalid or corrupted PDF file") from exc

    pages: list[str] = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text.strip())

    content = "\n\n".join(pages).strip()
    if not content:
        raise BadRequestError("No text could be extracted from the PDF. Try a text-based PDF.")

    return content
