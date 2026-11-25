import logging
import re
import smtplib
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.email_services import send_email
from app.file_reader import read_resume
from app.gap_node import analyze_gap
from app.graph import build_graph
from app.job_info import extract_company
from app.resume_builder import OUTPUT_DIR, make_filename, save_resume_pdf
from app.schema import UserAnswer
import os

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
logger = logging.getLogger("naukri_mitra")

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD = 5 * 1024 * 1024
MIN_JD = 100
MAX_JD = 20000
MIN_DETAIL = 15
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[A-Za-z]{2,}$")

app = FastAPI(title="Naukri Mitra")
graph = build_graph()

# In-memory sessions (fine for a local single-user app; they reset on server restart)
SESSIONS: dict[str, dict] = {}


# ---------- request models ----------

class AnswerIn(BaseModel):
    question: str
    answer: str = ""
    confirmed: bool = False


class GenerateIn(BaseModel):
    session_id: str
    answers: list[AnswerIn] = []


class SendIn(BaseModel):
    session_id: str
    to_email: str
    subject: str
    body: str


def get_session(session_id: str) -> dict:
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(404, "Session expired. Please start again.")
    return session


# ---------- API ----------

@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/analyze")
def analyze(resume: UploadFile = File(...), jd: str = Form(...)):
    jd = jd.strip()
    if len(jd) < MIN_JD:
        raise HTTPException(400, "Please paste the full job description.")
    if len(jd) > MAX_JD:
        raise HTTPException(400, "The job description is too long.")

    data = resume.file.read(MAX_UPLOAD + 1)
    if len(data) > MAX_UPLOAD:
        raise HTTPException(400, "The file is larger than 5 MB.")
    if not data.startswith(b"%PDF"):
        raise HTTPException(400, "Please upload a valid PDF file.")

    session_id = uuid.uuid4().hex
    path = UPLOAD_DIR / f"{session_id}.pdf"
    path.write_bytes(data)

    try:
        resume_text = read_resume(str(path))
    except Exception:
        logger.exception("Could not read the PDF")
        raise HTTPException(400, "Could not read this PDF.")
    finally:
        try:
            path.unlink(missing_ok=True)   # do not keep the user's resume on disk
        except OSError:
            pass

    try:
        report = analyze_gap(resume_text, jd)
    except Exception:
        logger.exception("Gap analysis failed")
        raise HTTPException(502, "The AI service had a problem. Please try again.")

    if len(SESSIONS) > 200:
        SESSIONS.pop(next(iter(SESSIONS)))

    SESSIONS[session_id] = {"resume_text": resume_text, "jd": jd, "report": report}

    return {
        "session_id": session_id,
        "match_score": report.match_score,
        "matching_skills": report.matching_skills,
        "missing_skills": report.missing_skills,
        "sections_to_improve": report.sections_to_improve,
        "questions": report.questions_for_user[:6],
    }


@app.post("/api/generate")
def generate(payload: GenerateIn):
    session = get_session(payload.session_id)

    # Honesty guardrail, enforced on the server too
    answers = []
    for a in payload.answers:
        detail = a.answer.strip()
        if a.confirmed and len(detail) < MIN_DETAIL:
            raise HTTPException(400, f"Please add more detail for: {a.question}")
        answers.append(
            UserAnswer(
                question=a.question,
                answer=detail if a.confirmed else "",
                confirmed=a.confirmed,
            )
        )

    try:
        result = graph.invoke(
            {
                "resume": session["resume_text"],
                "jd": session["jd"],
                "report": session["report"],
                "answers": answers,
            }
        )
    except Exception:
        logger.exception("Agent run failed")
        raise HTTPException(502, "The AI service had a problem. Please try again.")

    new_resume = result["new_resume"]
    check = result["check"]
    draft = result.get("email_draft")

    company = ""
    try:
        company = extract_company(session["jd"])
    except Exception:
        logger.warning("Could not extract the company name", exc_info=True)

    candidate = new_resume.strip().splitlines()[0]
    filename = make_filename(candidate, company)

    try:
        pdf_path = save_resume_pdf(new_resume, filename)
    except Exception:
        logger.exception("PDF creation failed")
        raise HTTPException(500, "Could not create the PDF.")

    session["pdf_path"] = pdf_path
    session["is_safe"] = check.is_safe

    return {
        "demo": DEMO_MODE,
        "is_safe": check.is_safe,
        "unsupported_claims": check.unsupported_claims,
        "pdf_url": f"/files/{filename}?v={int(time.time())}",
        "filename": filename,
        "to_email": result.get("to_email", ""),
        "to_emails": result.get("emails", []),
        "subject": draft.subject if draft else "",
        "body": draft.body if draft else "",
    }


@app.post("/api/send")
def send(payload: SendIn):
    if DEMO_MODE:
        raise HTTPException(403, "Sending is disabled in the public demo.")
    session = get_session(payload.session_id)

    if not session.get("is_safe") or not session.get("pdf_path"):
        raise HTTPException(400, "This resume did not pass the fact-check, so it cannot be sent.")

    to_email = payload.to_email.strip()
    subject = payload.subject.strip()
    body = payload.body.strip()

    if not EMAIL_RE.fullmatch(to_email):
        raise HTTPException(400, "Please enter a valid recipient email.")
    if not subject or not body:
        raise HTTPException(400, "Subject and message cannot be empty.")
    if re.search(r"[\r\n]", subject):
        raise HTTPException(400, "The subject must be a single line.")

    try:
        send_email(to_email, subject, body, session["pdf_path"])
    except ValueError:
        logger.exception("Email is not configured")
        raise HTTPException(500, "Gmail credentials are missing. Check your .env file.")
    except smtplib.SMTPAuthenticationError:
        logger.exception("Gmail login failed")
        raise HTTPException(502, "Gmail login failed. Check your App Password in .env.")
    except Exception:
        logger.exception("Sending failed")
        raise HTTPException(502, "Could not send the email. Please try again.")

    return {"ok": True}


# ---------- files and frontend ----------

app.mount("/files", StaticFiles(directory=OUTPUT_DIR), name="files")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def home():
    return FileResponse(FRONTEND_DIR / "index.html")