from typing import TypedDict, List
from app.schema  import GapReport, UserAnswer, FactCheck, EmailDraft


class AgentState(TypedDict, total=False):
    resume : str
    jd: str
    report : GapReport
    answers : List[UserAnswer]
    new_resume : str
    check : FactCheck
    attempts : int
    emails: List[str]
    to_email: str
    email_draft: EmailDraft