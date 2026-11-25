from app.schema import UserAnswer
import re

MIN_LENGTH = 15

def collect_answer(question : list[str]) -> list[UserAnswer]:
    answers = []
    for q in question:
        print(f"\n{q}")
        has_it = input("Do you have this skills? (y/n): ").strip().lower() == "y"
        detail = ""
        if has_it:
            while len(detail) < MIN_LENGTH:
                detail = input("" \
                "What Exactly did you do ? (tool/platform name, where you used it)"
                "[type 'skip] to drop this skill]: ").strip()
                if detail.lower()== "skip":
                        has_it = False
                        detail = ""
                        break

        answers.append(UserAnswer(question=q, answer=detail, confirmed=has_it))
    return answers  

EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[A-Za-z]{2,}")


def ask_recipient(emails: list[str]) -> str:
    if len(emails) > 1:
        print("Multiple email ids found in the JD:")
        for i, e in enumerate(emails, 1):
            print(f"{i}. {e}")
        choice = input("Enter the number of the email to use: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(emails):
            return emails[int(choice) - 1]

    while True:
        print("Email id is not mentioned in the JD.")
        email = input("Enter the recipient email id: ").strip()
        if EMAIL_RE.fullmatch(email):
            return email
        print("That does not look like a valid email id. Try again.") 