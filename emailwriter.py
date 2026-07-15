"""
Synapse Module 4 - EMAIL formatter.

NOTE: To save tokens, the email is now generated inside brain.py in the SAME
Gemini call as the brief (no separate LLM request). This module just reads that
result and formats it cleanly. No API call here = no extra cost.

RULE (Digitograffi playbook): no em/en dash, plain hyphen only.
"""


def _strip_dashes(text: str) -> str:
    if not text:
        return text
    for ch in ("—", "–", "−", "‒"):  # em, en, minus, figure dash
        text = text.replace(ch, "-")
    return text


def draft(company: str, playbook: dict, brain: dict, triggers: dict = None) -> dict:
    """Read subject/body from the brain result, clean it, add source."""
    sender = playbook["company"]["name"]

    subject = brain.get("email_subject") or f"{company} - a quick idea from {sender}"
    body = brain.get("email_body") or ""
    if not body:
        service = brain.get("recommended_service", "digital marketing and AI automation")
        body = (
            f"Hi {company} team,\n\n{brain.get('pitch_angle','')}\n\n"
            f"At {sender} we do digital marketing, AI tool automation and AI "
            f"development in one place. We would start with {service}.\n\n"
            f"Open to a quick 15-minute chat this week?\n\nBest,\n{sender}"
        )

    # find one source link from triggers (for the "hook source" note)
    source = ""
    for kind in ("funding", "hiring", "news", "leadership"):
        items = (triggers or {}).get(kind) or []
        if items:
            source = items[0]["link"]
            break

    return {
        "ok": True,
        "subject": _strip_dashes(subject),
        "body": _strip_dashes(body),
        "source": source,
        "_ai": not brain.get("_fallback", False),
    }


if __name__ == "__main__":
    import json
    pb = json.loads(open("playbook.json", encoding="utf-8").read())
    fake_brain = {
        "recommended_service": "AI Tool Automation",
        "pitch_angle": "Active hiring spotted - a good moment to automate.",
        "email_subject": "Acme - a quick idea",
        "email_body": "Hi Acme team, ...",
    }
    out = draft("Acme Corp", pb, fake_brain, {})
    print("SUBJECT:", out["subject"])
    print(out["body"])
