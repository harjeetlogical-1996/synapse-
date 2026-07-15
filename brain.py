"""
Synapse Module 3 - BRAIN (the actual AI).

Takes search (triggers) + techstack (website) + PLAYBOOK and asks Gemini for:
  - pitch angle (which Digitograffi service, and why)
  - talking points, what to avoid
  - buying committee
  - AND the outreach email  <-- all in ONE call (token-saving)

Why one call: two separate LLM calls cost ~2x the tokens. We ask Gemini for
the brief and the email together, so a single request does both.

The intelligence is specific (not generic) because Gemini gets the PLAYBOOK,
so it knows what WE (Digitograffi) sell.

GUARDRAIL: the model is told not to invent facts. Only use what's in the
triggers/website. Every claim carries a source.

No key -> a clean rule-based fallback, so the tool runs without a key too.
"""
import json
import urllib.request

import config

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:generateContent?key={key}"
)


def _triggers_text(triggers: dict, limit_per_kind: int = 2) -> str:
    """Compact trigger text for the prompt (kept short to save tokens)."""
    lines = []
    for kind, items in (triggers or {}).items():
        for it in (items or [])[:limit_per_kind]:
            lines.append(f"- [{kind}] {it['title']} | src: {it['link']}")
    return "\n".join(lines) if lines else "(no trigger events found)"


def _tech_text(tech_res: dict) -> str:
    tech = tech_res.get("tech") or []
    if not tech:
        return "(no tech signals)"
    return ", ".join(t["name"] for t in tech)


def _build_prompt(company: str, playbook: dict, triggers: dict, tech_res: dict) -> str:
    """Compact prompt - short on purpose to keep token cost low."""
    pb = playbook
    services = "; ".join(s["service"] for s in pb.get("what_we_sell", []))
    ideal = pb.get("ideal_customer", {}).get("description", "")

    return f"""You are a sales research assistant for {pb['company']['name']} ({pb['company']['one_liner']}).
We sell: {services}.
Ideal customer: {ideal}

TARGET COMPANY: {company}
Website tech: {_tech_text(tech_res)}
Website title: {tech_res.get('title','')}
Trigger events (with sources):
{_triggers_text(triggers)}

Return ONLY this JSON. Do not invent facts; if unknown, write "unknown".
Base everything on the signals above. Be specific and useful to a real rep.
{{
 "snapshot":"2 lines - what this company does, industry, rough size/stage",
 "fit_score":"high|medium|low",
 "fit_reason":"1 line - why they fit (or not) for us",
 "recommended_service":"one of our services",
 "pitch_angle":"2 lines - which signal to open with and the core message",
 "pain_points":["likely pain 1 inferred from signals","pain 2","pain 3"],
 "talking_points":["specific point 1","point 2","point 3","point 4"],
 "opener":"1 personalized ice-breaker line a rep can say on a call or email",
 "discovery_questions":["MEDDICC-style question 1","question 2","question 3"],
 "objections":[{{"objection":"likely pushback","response":"how to handle it"}},{{"objection":"another","response":"handle"}}],
 "buying_committee":[{{"role":"title likely to decide","why":"their concern"}}],
 "competitor_angle":"1 line - if a competitor/incumbent is implied, how to position; else 'unknown'",
 "best_channel":"email|linkedin|call - which to use and why, 1 line",
 "next_action":"1 clear next step the rep should take now",
 "what_to_avoid":"1 line - what NOT to do with this account",
 "confidence":"high|medium|low",
 "email_subject":"short subject line",
 "email_body":"70-110 word cold email. Open with the trigger if any. Lead ONE service. Warm, human, not spammy. Plain hyphens only, no em dash."
}}"""


def _call_gemini(prompt: str) -> dict:
    if not config.have_gemini():
        return None
    url = GEMINI_URL.format(model=config.GEMINI_MODEL, key=config.GEMINI_API_KEY)
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        # ceiling for the richer JSON, still bounded to keep cost low
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 1600},
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={"content-type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=40) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = ""
        for cand in data.get("candidates", []):
            for part in cand.get("content", {}).get("parts", []):
                text += part.get("text", "")
        text = text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:]
        return json.loads(text)
    except Exception:
        return None


def _fallback(company: str, playbook: dict, triggers: dict, tech_res: dict) -> dict:
    """No-Gemini rule-based brief + email. For test/demo without a key."""
    has_funding = bool((triggers or {}).get("funding"))
    has_hiring = bool((triggers or {}).get("hiring"))
    tech = tech_res.get("tech") or []
    tech_names = ", ".join(t["name"] for t in tech) if tech else "unknown"
    sender = playbook["company"]["name"]

    if has_funding:
        service = "AI Tool Automation + Growth Marketing"
        angle = "Recent funding spotted - a good moment for growth marketing and automating processes as they scale."
    elif has_hiring:
        service = "AI Tool Automation"
        angle = "Active hiring spotted - they are scaling, so automating repetitive work can keep the team efficient."
    else:
        service = "Digital Marketing"
        angle = "General angle to improve online presence and lead generation."

    body = (
        f"Hi {company} team,\n\n{angle}\n\n"
        f"At {sender} we do digital marketing, AI tool automation and AI development "
        f"in one place. For a team like yours we would start with {service}.\n\n"
        f"Open to a quick 15-minute chat this week?\n\nBest,\n{sender}"
    )

    return {
        "snapshot": f"{company}. Details limited (no AI key set). Tech seen: {tech_names}.",
        "fit_score": "medium",
        "fit_reason": "Rule-based estimate (no Gemini key).",
        "recommended_service": service,
        "pitch_angle": angle,
        "pain_points": [
            "Scaling without enough automation" if has_hiring else "Growth / visibility gaps",
            "Manual work eating team time",
            "unknown",
        ],
        "talking_points": [
            f"Website tech: {tech_names}",
            "Funding signal" if has_funding else ("Hiring signal" if has_hiring else "General outreach"),
            "Digitograffi offers marketing + AI automation + AI dev in one place",
            "One partner instead of three separate vendors",
        ],
        "opener": f"Saw what's happening at {company} - had a quick idea for you.",
        "discovery_questions": [
            "What is slowing your team down the most right now?",
            "Who owns marketing and automation decisions?",
            "unknown",
        ],
        "objections": [
            {"objection": "We already have an agency", "response": "We add AI automation most agencies do not offer."},
            {"objection": "Not the right time", "response": "Start with one small automation, no big commitment."},
        ],
        "buying_committee": [
            {"role": "Founder/CEO", "why": "Owns growth and budget"},
            {"role": "Marketing head", "why": "Owns the outcome"},
        ],
        "competitor_angle": "unknown",
        "best_channel": "email - low friction first touch",
        "next_action": "Send the drafted email and follow up in 3 days.",
        "what_to_avoid": "Do not cram all three services; pick one angle.",
        "confidence": "low",
        "email_subject": f"{company} - a quick idea from {sender}",
        "email_body": body,
        "_fallback": True,
    }


def analyze(company: str, playbook: dict, triggers: dict, tech_res: dict) -> dict:
    """Brief + email in one shot. Gemini if key, else rule-based fallback."""
    prompt = _build_prompt(company, playbook, triggers, tech_res)
    result = _call_gemini(prompt)
    if result is None:
        result = _fallback(company, playbook, triggers, tech_res)
    return result


if __name__ == "__main__":
    pb = json.loads(open("playbook.json", encoding="utf-8").read())
    fake_triggers = {"hiring": [{"title": "Acme is hiring 20 engineers", "link": "http://example.com/jobs"}]}
    fake_tech = {"tech": [{"name": "WordPress", "category": "CMS"}], "title": "Acme Corp"}
    out = analyze("Acme Corp", pb, fake_triggers, fake_tech)
    print(json.dumps(out, indent=2, ensure_ascii=False))
