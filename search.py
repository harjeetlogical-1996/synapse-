"""
Synapse Module 1 - SEARCH (trigger events dhoondhna).

Company ka naam leta hai aur Google (Serper.dev) pe dhoondhta hai:
funding, hiring, news, leadership change. Ye "trigger events" hain - baat
shuru karne ke bahaane.

RULE: har finding ke saath uska SOURCE (title + link) rakhta hai. Bina source
kuch nahi. Ye guardrail brief ko bharosemand banata hai.

Pure stdlib (urllib) - koi extra library nahi.
Serper na ho to khali list + saaf note lautaata hai, crash nahi.
"""
import json
import urllib.request
import urllib.error

import config

SERPER_URL = "https://google.serper.dev/search"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) synapse/0.1"

# Har trigger type ke liye ek focused query. {c} = company ka naam.
_QUERIES = {
    "funding":    '"{c}" (funding OR raised OR investment OR "series")',
    "hiring":     '"{c}" (hiring OR "we are hiring" OR careers OR jobs)',
    "news":       '"{c}" (news OR launch OR announcement OR expansion)',
    "leadership": '"{c}" (CEO OR "new CTO" OR "appointed" OR "joins as")',
}


def _post(query: str) -> dict:
    """Ek search query bhejo, JSON wapas. Error pe {} lautao."""
    body = json.dumps({
        "q": query,
        "num": config.SEARCH_RESULTS,
        "gl": config.SEARCH_GL,
        "hl": config.SEARCH_HL,
    }).encode("utf-8")
    req = urllib.request.Request(
        SERPER_URL, data=body, method="POST",
        headers={
            "X-API-KEY": config.SERPER_API_KEY,
            "Content-Type": "application/json",
            "User-Agent": UA,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError):
        return {}


def _extract(results: dict, limit: int = 3) -> list:
    """Serper ke 'organic' se sirf title/link/snippet nikaalo."""
    out = []
    for item in (results.get("organic") or [])[:limit]:
        title = (item.get("title") or "").strip()
        link = (item.get("link") or "").strip()
        snippet = (item.get("snippet") or "").strip()
        if title and link:
            out.append({"title": title, "link": link, "snippet": snippet})
    return out


def find_triggers(company: str) -> dict:
    """
    Company ke liye trigger events dhoondho.

    Returns:
        {
          "ok": bool,                 # search chala ya nahi
          "note": str,                # agar kuch problem hui to
          "triggers": {
              "funding":    [ {title, link, snippet}, ... ],
              "hiring":     [ ... ],
              "news":       [ ... ],
              "leadership": [ ... ],
          }
        }
    """
    company = (company or "").strip()
    if not company:
        return {"ok": False, "note": "Company name is empty.", "triggers": {}}

    if not config.have_serper():
        return {
            "ok": False,
            "note": "No SERPER_API_KEY - search skipped. Add the key in .env.",
            "triggers": {},
        }

    triggers = {}
    for kind, template in _QUERIES.items():
        data = _post(template.format(c=company))
        triggers[kind] = _extract(data)

    total = sum(len(v) for v in triggers.values())
    return {
        "ok": True,
        "note": f"{total} signals found." if total else "No clear trigger found.",
        "triggers": triggers,
    }


# Akela test karne ke liye:  python search.py "Company Name"
if __name__ == "__main__":
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else "Freshworks"
    print(f"Searching triggers for: {name}\n")
    res = find_triggers(name)
    print("OK:", res["ok"], "|", res["note"], "\n")
    for kind, items in res["triggers"].items():
        print(f"[{kind.upper()}]")
        if not items:
            print("  (kuch nahi mila)")
        for it in items:
            print(f"  - {it['title']}")
            print(f"    {it['link']}")
        print()
