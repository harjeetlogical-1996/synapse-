"""
Synapse - step-by-step agent runner.

run.py CLI ke liye tha. Ye module server ke liye hai - ek generator jo har
step ka result yield karta hai, taaki frontend live progress dikha sake.
"""
import json
from pathlib import Path

import config
import search
import techstack
import brain
import intent
import emailwriter
import brief


def load_playbook() -> dict:
    return json.loads(Path(__file__).with_name("playbook.json").read_text(encoding="utf-8"))


def build_playbook_override(name, one_liner, services_text, ideal):
    """Turn simple frontend inputs into a full playbook dict.

    services_text: one service per line (e.g. "Digital Marketing\nAI Development")
    Lets the user test different company profiles without editing the file.
    """
    base = load_playbook()
    if name:
        base["company"]["name"] = name
    if one_liner:
        base["company"]["one_liner"] = one_liner
    if services_text:
        services = []
        for line in services_text.splitlines():
            line = line.strip()
            if line:
                services.append({"service": line, "pitch": ""})
        if services:
            base["what_we_sell"] = services
    if ideal:
        base.setdefault("ideal_customer", {})["description"] = ideal
    return base


def run_steps(company: str, website: str = "", playbook: dict = None):
    """
    Generator - har step pe ek dict yield karta hai:
        {"step": 1, "key": "search", "title": "...", "status": "done|skip",
         "detail": "...", "data": {...}}
    Aakhri yield: {"step": "final", "brief_html": "...", "brief_path": "..."}
    """
    pb = playbook or load_playbook()
    if not website:
        website = company

    ctx = {"triggers": {}, "tech": {}, "brain": {}, "email": {}}

    # Step 1: Search
    trig = search.find_triggers(company)
    ctx["triggers"] = trig.get("triggers", {})
    total = sum(len(v) for v in ctx["triggers"].values())
    yield {
        "step": 1, "key": "search", "title": "Find trigger events",
        "status": "done" if trig.get("ok") else "skip",
        "detail": trig.get("note", ""),
        "data": {"count": total, "triggers": ctx["triggers"]},
    }

    # Step 2: Tech stack
    tech = techstack.detect(website)
    ctx["tech"] = tech
    yield {
        "step": 2, "key": "techstack", "title": "Scan website / tech stack",
        "status": "done" if tech.get("ok") else "skip",
        "detail": tech.get("note", ""),
        "data": {"tech": tech.get("tech", []), "title": tech.get("title", "")},
    }

    # Step 3: Brain
    br = brain.analyze(company, pb, ctx["triggers"], ctx["tech"])
    ctx["brain"] = br
    tag = "rule-based" if br.get("_fallback") else "Gemini AI"
    yield {
        "step": 3, "key": "brain", "title": "Think — pitch angle",
        "status": "done",
        "detail": f"{br.get('recommended_service','-')} · {tag}",
        "data": {
            "fit_score": br.get("fit_score"),
            "recommended_service": br.get("recommended_service"),
            "pitch_angle": br.get("pitch_angle"),
            "ai": not br.get("_fallback"),
        },
    }

    # Step 4: Intent score (buying-signal score from data we already have)
    intent_res = intent.score(ctx["triggers"], ctx["tech"], br)
    ctx["intent"] = intent_res
    yield {
        "step": 4, "key": "intent", "title": "Score buying intent",
        "status": "done",
        "detail": f"{intent_res['score']}/100 · {intent_res['level']}",
        "data": {"score": intent_res["score"], "level": intent_res["level"]},
    }

    # Step 5: Email
    em = emailwriter.draft(company, pb, br, ctx["triggers"])
    ctx["email"] = em
    yield {
        "step": 5, "key": "email", "title": "Draft outreach email",
        "status": "done",
        "detail": em.get("subject", ""),
        "data": {"subject": em.get("subject"), "ai": em.get("_ai", False)},
    }

    # Step 6: Brief
    html_str = brief.build(company, pb, ctx["triggers"], ctx["tech"], br, em, intent_res)
    path = brief.save(html_str, company)
    yield {
        "step": 6, "key": "brief", "title": "Build account brief",
        "status": "done",
        "detail": f"Saved: {path}",
        "data": {},
    }

    # Final
    yield {
        "step": "final",
        "brief_html": html_str,
        "brief_path": str(path),
        "company": company,
        "keys": {"serper": config.have_serper(), "gemini": config.have_gemini()},
    }
