import re

EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
IGNORE_PREFIXES = ("noreply", "no-reply", "donotreply")


def extract_emails(jd: str) -> list[str]:
    found = EMAIL_PATTERN.findall(jd)
    unique = []
    for email in found:
        e = email.lower()
        if e.startswith(IGNORE_PREFIXES):
            continue
        if e not in unique:
            unique.append(e)
    return unique