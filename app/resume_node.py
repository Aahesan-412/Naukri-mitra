from app.llm import get_llm
from app.schema import GapReport,UserAnswer

RESUME_PROMPT = """
You are an expert resume writer. Rewrite the RESUME so it fits the JOB DESCRIPTION.

Strict rules:
- Use ONLY facts found in the original resume or in the CONFIRMED USER ANSWERS.
- Never invent skills, tools, tools versions, years, metrics, companies or projects.
- From a confirmed answer, use only what the user actually wrote. Do not add
  details (service names, numbers, tools) that the user did not mention.
- Do not add anything from the MISSING SKILLS list unless it appears in the
  confirmed answers.
- You may reorder sections, reword bullets, and use the JD's keywords only where
  they truthfully describe the user's existing work.
- Keep it ATS-friendly: plain text, standard headings (Summary, Skills,
  Experience, Projects, Education), no tables, no columns.
- Keep contact details exactly as they are in the original resume.
- Output only the final resume text, with no explanation.

- Do not upgrade wording. If the original says "comfortable" or "familiar", do not change it to "expert" or "experienced".
- Keep every skill from the original resume. You may reorder them but not drop them.
- Do not copy sentences from the job description into the resume.
- Do not add a closing tagline or objective line at the end.
- Output plain text only. No markdown symbols such as ** or #.
- Never add a new job, internship, freelance work, project, certificate or section that is not in the original resume. If the JD asks for experience the candidate does not have, simply ignore that requirement.
- Keep exactly the same experience and project entries as the original. You may reorder them and reword bullets, but you may not add entries.
- The new resume must not be longer than the original. Use at most 3 bullets per experience or project, each one or two lines. Do not add extra sections or extra bullets.
ORIGINAL RESUME:
{resume}

JOB DESCRIPTION:
{jd}

MISSING SKILLS (do not add unless confirmed):
{missing}

CONFIRMED USER ANSWERS:
{confirmed}

{feedback_block}
"""

def format_confirmed(answers: list[UserAnswer]) -> str:
    lines = [f"- Q: {a.question}\n  A: {a.answer}" for a in answers if a.confirmed]
    return "\n".join(lines) if lines else "None"


def write_resume(resume, jd, report, answers, feedback=None) -> str:
    llm = get_llm()

    feedback_block = ""
    if feedback:
        feedback_block = (
            "PREVIOUS ATTEMPT WAS REJECTED. Remove or fix these unsupported claims:\n"
            + "\n".join(f"- {c}" for c in feedback)
        )

    prompt = RESUME_PROMPT.format(
        resume=resume,
        jd=jd,
        missing="\n".join(f"- {s}" for s in report.missing_skills),
        confirmed=format_confirmed(answers),
        feedback_block=feedback_block,
    )
    return llm.invoke(prompt).content