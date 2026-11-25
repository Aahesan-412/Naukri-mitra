import fitz

def read_pdf(path: str) -> str:
    doc = fitz.open(path)
    text = ""
    for page in doc:
        text += page.get_text("text", sort=True) + "\n"
    return text.strip()

def read_resume(path: str) -> str:
    if path.lower().endswith(".pdf"):
        return read_pdf(path)
    else:
        raise ValueError("Only PDF files are allowed")
