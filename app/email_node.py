from app.llm import get_llm
from app.schema import EmailDraft

EMAIL_PROMPT = """
You write short, professional job application emails.

Write an email from the candidate to the hiring team.

Rules:
- Use ONLY facts from the RESUME. Do not invent skills, numbers or experience.
- Mention the role and company only if they appear in the JOB DESCRIPTION.
  If the company name is unknown, address it to "Hiring Team".
- 90 to 130 words in the body. Plain text, no markdown.
- Mention 2 or 3 of the most relevant strengths for this role.
- Say the resume is attached.
- End with the candidate's name, phone and email taken from the resume.
- subject must be short and include the role and the candidate's name.
- Do not upgrade wording. Never use words like "expertise", "expert", "proficient", "production-ready", "extensive" or "strong" unless the resume itself uses them.
- Describe projects exactly as the resume names them. Do not rename or reinterpret a project.
- The candidate is a fresher: use modest, honest wording such as "hands-on experience", "worked on", "built".
RESUME:
{resume}

JOB DESCRIPTION:
{jd}

Respond with a JSON object in exactly this shape:
{{"subject": "...", "body": "..."}}
"""


def write_email(resume: str, jd: str, retries: int = 3) -> EmailDraft:
    llm = get_llm().with_structured_output(EmailDraft, method="json_mode")
    prompt = EMAIL_PROMPT.format(resume=resume, jd=jd)

    last_error = None
    for _ in range(retries):
        try:
            return llm.invoke(prompt)
        except Exception as e:
            last_error = e
    raise last_error