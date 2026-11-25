from pydantic import BaseModel, Field
from typing import List

class GapReport(BaseModel):
    match_score: int = Field(description="Integer score from 0 to 100")
    matching_skills: List[str] = Field(
        description="JSON array of short strings, one skill per item"
    )
    missing_skills: List[str] = Field(
        description="JSON array of short strings. Skills in JD but not in resume"
    )
    sections_to_improve: List[str] = Field(
        description="JSON array of short strings, one suggestion per item. "
                    "Always an array, even if there is only one suggestion."
    )
    questions_for_user: List[str] = Field(
        description="JSON array of short questions, one per item"
    )



class UserAnswer(BaseModel):
    question : str
    answer : str
    confirmed : bool


class FactCheck(BaseModel):
    unsupported_claims: List[str] = Field(
        default_factory=list,
        description="JSON array of short strings. Claims in the new resume that are "
                    "not supported by the original resume or the confirmed answers. "
                    "Return an empty array if everything is supported."
    )

    @property
    def is_safe(self) -> bool:
        return len(self.unsupported_claims) == 0


class EmailDraft(BaseModel):
    subject: str
    body: str