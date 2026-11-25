from pypdf import PdfReader
# from docx import Document
import fitz


def read_pdf(path: str) -> str:
    doc = fitz.open(path)
    text = ""
    for page in doc:
        text += page.get_text("text", sort=True) + "\n"
    return text.strip()


def read_docx(path: str)  -> str:
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs).strip()


def read_resume(path: str) -> str:
    if path.lower().endswith(".pdf"):
        return read_pdf(path)
    elif path.lower().endswith(".docx"):
        return read_docx(path)
    else:
        raise ValueError("Only Allow PDF or DOCX Files")

    