from pydantic import BaseModel, Field

from app.llm import get_llm


class CompanyInfo(BaseModel):
    company: str = Field(
        default="",
        description="Company name from the JD, empty string if not mentioned",
    )


COMPANY_PROMPT = """
Extract the hiring company name from this job description.
Use only what is written in it. If the company name is not mentioned, use an empty string.

Respond with a JSON object in exactly this shape:
{{"company": "..."}}

JOB DESCRIPTION:
{jd}
"""


def extract_company(jd: str, retries: int = 3) -> str:
    llm = get_llm().with_structured_output(CompanyInfo, method="json_mode")
    prompt = COMPANY_PROMPT.format(jd=jd)

    last_error = None
    for _ in range(retries):
        try:
            return llm.invoke(prompt).company
        except Exception as e:
            last_error = e
    raise last_error