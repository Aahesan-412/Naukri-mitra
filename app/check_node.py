from app.llm import get_llm
from app.schema import FactCheck, UserAnswer
from app.resume_node import format_confirmed

CHECK_PROMPT = """
You are a strict fact-checker for resumes.

Compare the NEW RESUME against the ORIGINAL RESUME and the CONFIRMED USER ANSWERS.
List every claim in the new resume that is NOT supported by those two sources.
Check skills, tools, numbers, years, job titles, companies and wording that
exaggerates the original (for example "comfortable" changed to "expert").
Ignore pure reordering and harmless rewording.
Every list field must be a JSON array of short strings.

- A new category label that only groups skills or projects already present in the
  original resume (for example "Computer Vision" for a CNN image project) is NOT
  an unsupported claim. Flag only new tools, new experience, new numbers, or
  exaggerated wording.
Respond with a JSON object in exactly this shape:
{{"unsupported_claims": ["claim 1", "claim 2"]}}
Use an empty array if every claim is supported.
ORIGINAL RESUME:
{original}

CONFIRMED USER ANSWERS:
{confirmed}

NEW RESUME:
{new_resume}
"""


def check_resume(original: str, new_resume: str, answers: list[UserAnswer], retries: int = 3) -> FactCheck:
    llm = get_llm().with_structured_output(FactCheck, method="json_mode")
    prompt = CHECK_PROMPT.format(
        original=original,
        confirmed=format_confirmed(answers),
        new_resume=new_resume,
    )

    last_error = None
    for _ in range(retries):
        try:
            return llm.invoke(prompt)
        except Exception as e:
            last_error = e
    raise last_error    