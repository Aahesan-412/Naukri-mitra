from app.llm import get_llm
from app.schema import GapReport

GAP_PROMPT = """
You are an expert technical recruiter and resume reviewer.

Compare the RESUME with the JOB DESCRIPTION.

Rules:
- Only use facts present in the resume. Never invent skills or experience.
- Be specific and short.

- Every list field must be a JSON array of short strings (one item per string). Never return a paragraph in place of a list.

- questions_for_user must only be about technical skills, tools or experience. Do not ask about schedules, commitments or logistics.
RESUME:
{resume}

JOB DESCRIPTION:
{jd}
"""

def analyze_gap(resume: str, jd: str, retries: int = 3 ) -> GapReport:
    llm = get_llm().with_structured_output(GapReport)
    prompt = GAP_PROMPT.format(resume=resume, jd=jd)

    last_error = None
    for _ in range(retries):
        try:
            return llm.invoke(prompt)
        except Exception as e:
            last_error = e
    raise last_error