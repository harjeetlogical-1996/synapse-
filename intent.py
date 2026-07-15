"""
Synapse Agent - INTENT (buying-signal score).

From the AI Sales OS vision: "Detect buying signals and intent score."

Takes the trigger events (from search) + tech stack + the brain's fit, and
produces one number: how ready is this account to buy, right now (0-100),
plus the concrete signals behind it.

This runs on data we ALREADY have (Research Agent output) - no new API call,
no new access. Cheap and instant.

Scoring is rule-based and transparent (every point has a reason), so a rep can
trust it. Not a black box.
"""

# Weight of each signal type toward the intent score.
# Funding and hiring are the strongest "they have budget / are scaling" signals.
_SIGNAL_WEIGHTS = {
    "funding": 30,      # raised money -> budget to spend
    "hiring": 25,       # scaling -> needs tools/systems
    "news": 15,         # active / in motion
    "leadership": 20,   # new exec -> new priorities, new budget
}

# Fit multiplier: a great-fit account with signals matters more than a
# poor-fit account with the same signals.
_FIT_MULTIPLIER = {"high": 1.0, "medium": 0.8, "low": 0.5}


def score(triggers: dict, tech_res: dict, brain: dict) -> dict:
    """
    Compute a buying-intent score from existing research data.

    Returns:
      {
        "score": int,            # 0-100
        "level": "hot|warm|cool|cold",
        "signals": [ {label, points, source}, ... ],   # what drove it
        "summary": str,
      }
    """
    signals = []
    raw = 0

    for kind, weight in _SIGNAL_WEIGHTS.items():
        items = (triggers or {}).get(kind) or []
        if not items:
            continue
        # first hit = full weight; extra hits add a small bonus (capped)
        count = len(items)
        pts = weight + min(count - 1, 2) * 4
        raw += pts
        signals.append({
            "label": _label(kind, count),
            "points": pts,
            "source": items[0].get("link", ""),
        })

    # tech stack presence = a small "they invest in tooling" nudge
    tech = tech_res.get("tech") or []
    if tech:
        pts = min(len(tech) * 2, 8)
        raw += pts
        signals.append({
            "label": f"Runs {len(tech)} detectable tools (active tech buyer)",
            "points": pts,
            "source": "",
        })

    # apply fit multiplier
    fit = str(brain.get("fit_score", "medium")).lower()
    mult = _FIT_MULTIPLIER.get(fit, 0.8)
    final = int(min(round(raw * mult), 100))

    level, summary = _bucket(final, fit, signals)

    return {
        "score": final,
        "level": level,
        "signals": sorted(signals, key=lambda s: -s["points"]),
        "summary": summary,
    }


def _label(kind: str, count: int) -> str:
    base = {
        "funding": "Recent funding (has budget to spend)",
        "hiring": "Actively hiring (scaling, needs systems)",
        "news": "Recent news / activity (in motion)",
        "leadership": "Leadership change (new priorities & budget)",
    }[kind]
    if count > 1:
        base += f" · {count} signals"
    return base


def _bucket(final: int, fit: str, signals: list):
    if final >= 70:
        return "hot", "Strong buying intent - reach out now, this is a priority account."
    if final >= 45:
        return "warm", "Warm - real signals present, worth a personalized touch soon."
    if final >= 20:
        return "cool", "Cool - some activity, but not urgent. Nurture."
    if not signals:
        return "cold", "Cold - no clear buying signals found yet. Low priority for now."
    return "cold", "Cold - weak signals or poor fit. Deprioritize."


if __name__ == "__main__":
    fake_triggers = {
        "funding": [{"title": "Acme raised $20M", "link": "http://x.com/f"}],
        "hiring": [{"title": "Acme hiring 30", "link": "http://x.com/h"},
                   {"title": "Acme hiring sales", "link": "http://x.com/h2"}],
    }
    fake_tech = {"tech": [{"name": "HubSpot", "category": "CRM"}]}
    for fit in ("high", "medium", "low"):
        out = score(fake_triggers, fake_tech, {"fit_score": fit})
        print(f"fit={fit}: {out['score']} ({out['level']}) - {out['summary']}")
        for s in out["signals"]:
            print(f"   +{s['points']}  {s['label']}")
        print()
