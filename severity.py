import re

def extract_severity(text: str) -> str:
    if not text:
        return "low"

    match = re.search(
        r"Severity:\s*(High|Medium|Low|Urgent)",
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(1).lower()

    # fallback check
    if "urgent" in text.lower():
        return "urgent"

    return "low"
