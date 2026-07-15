"""
Synapse Research Agent - MAIN RUNNER.

Poora flow yahan judta hai:
  company naam do -> search -> techstack -> brain -> email -> brief

Use:
    python run.py "Company Name" [website.com]
    python run.py                (playbook ka test_account use karega, ya poochega)

Output: briefs/Company_Name.html  (browser mein khol ke dekho)
"""
import sys
import json
import webbrowser
from pathlib import Path

import config
import search
import techstack
import brain
import intent
import emailwriter
import brief


def load_playbook() -> dict:
    return json.loads(Path("playbook.json").read_text(encoding="utf-8"))


def run(company: str, website: str = "") -> str:
    pb = load_playbook()

    print(f"\n=== SYNAPSE Research Agent ===")
    print(f"Company : {company}")
    print(f"For     : {pb['company']['name']}")
    print("-" * 40)

    # Step 1: Search triggers
    print("1/5  Searching trigger events...")
    trig_res = search.find_triggers(company)
    print(f"     {trig_res['note']}")
    triggers = trig_res.get("triggers", {})

    # Step 2: Tech stack (website)
    if not website:
        website = company  # try the name as a domain (e.g. 'acme.com')
    print("2/5  Scanning website / tech stack...")
    tech_res = techstack.detect(website)
    print(f"     {tech_res['note']}")

    # Step 3: Brain (pitch + email in one call)
    print("3/5  Thinking (pitch angle)...")
    brain_res = brain.analyze(company, pb, triggers, tech_res)
    tag = "rule-based" if brain_res.get("_fallback") else "Gemini AI"
    print(f"     Recommended: {brain_res.get('recommended_service','-')}  ({tag})")

    # Step 4: Intent score (from data we already have)
    print("4/6  Scoring buying intent...")
    intent_res = intent.score(triggers, tech_res, brain_res)
    print(f"     {intent_res['score']}/100 ({intent_res['level']})")

    # Step 5: Email (formatted from the brain result, no extra API call)
    print("5/6  Drafting outreach email...")
    email_res = emailwriter.draft(company, pb, brain_res, triggers)
    print(f"     Subject: {email_res.get('subject','')}")

    # Step 6: Brief
    print("6/6  Building brief...")
    html_str = brief.build(company, pb, triggers, tech_res, brain_res, email_res, intent_res)
    path = brief.save(html_str, company)
    print("-" * 40)
    print(f"DONE. Brief saved: {path}")

    # health note
    if not config.have_serper():
        print("NOTE: No Serper key - triggers skipped. Add SERPER_API_KEY in .env.")
    if not config.have_gemini():
        print("NOTE: No Gemini key - rule-based brief. Add GEMINI_API_KEY in .env.")

    return path


def main():
    args = sys.argv[1:]
    company = args[0] if len(args) >= 1 else ""
    website = args[1] if len(args) >= 2 else ""

    if not company:
        pb = load_playbook()
        ta = pb.get("test_account", {})
        company = ta.get("name") or input("Company name daalo: ").strip()
        website = website or ta.get("website", "")

    if not company:
        print("Company name chahiye. Use: python run.py \"Company Name\" [website.com]")
        return

    path = run(company, website)

    # browser mein khol do
    try:
        webbrowser.open(Path(path).resolve().as_uri())
    except Exception:
        pass


if __name__ == "__main__":
    main()
