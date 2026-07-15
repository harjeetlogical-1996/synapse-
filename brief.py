"""
Synapse Module 5 - BRIEF BUILDER.

Sab modules (search + techstack + brain + email) ka output jodkr ek saaf
1-page account brief banata hai - HTML mein (browser mein khulta, PDF print
ho sakta). Har section source ke saath.

Ye "chehra" hai jo SDR ko dikhta hai. Isi pe demo tikta hai.
"""
import html
import json
from pathlib import Path


def _esc(s) -> str:
    return html.escape(str(s or ""))


def _pill(text: str, kind: str = "") -> str:
    return f'<span class="pill {kind}">{_esc(text)}</span>'


def _trigger_html(triggers: dict) -> str:
    labels = {"funding": "Funding", "hiring": "Hiring",
              "news": "News", "leadership": "Leadership"}
    blocks = []
    for kind, label in labels.items():
        items = (triggers or {}).get(kind) or []
        if not items:
            continue
        rows = ""
        for it in items:
            rows += (
                f'<li>{_esc(it["title"])}'
                f'<a href="{_esc(it["link"])}" target="_blank" rel="noopener">source</a></li>'
            )
        blocks.append(f'<div class="trig"><h4>{label}</h4><ul>{rows}</ul></div>')
    if not blocks:
        return '<p class="muted">Koi clear trigger event nahi mila.</p>'
    return '<div class="trigs">' + "".join(blocks) + "</div>"


def _tech_html(tech_res: dict) -> str:
    tech = tech_res.get("tech") or []
    if not tech:
        return '<p class="muted">Website se koi tech signal nahi mila.</p>'
    return "".join(_pill(f'{t["name"]} · {t["category"]}', "tech") for t in tech)


def _list_html(items) -> str:
    items = items or []
    if not items:
        return '<span class="muted">-</span>'
    return "<ul>" + "".join(f"<li>{_esc(x)}</li>" for x in items) + "</ul>"


def build(company: str, playbook: dict, triggers: dict, tech_res: dict,
          brain: dict, email: dict, intent: dict = None) -> str:
    """Build the full brief HTML string."""
    intent = intent or {}
    sender = playbook["company"]["name"]
    fit = brain.get("fit_score", "unknown")
    fit_kind = {"high": "hi", "medium": "mid", "low": "lo"}.get(str(fit).lower(), "")
    conf = brain.get("confidence", "unknown")
    ai_flag = "" if brain.get("_fallback") else "AI"
    src = email.get("source", "")

    initials = "".join(w[0] for w in company.split()[:2]).upper() or "?"
    fit_label = {"high": "Strong fit", "medium": "Possible fit", "low": "Weak fit"}.get(str(fit).lower(), str(fit))

    # intent score section
    intent_score = int(intent.get("score", 0))
    intent_level = str(intent.get("level", "cold")).lower()
    intent_deg = round(intent_score / 100 * 360)
    intent_sm = intent.get("summary", "")
    intent_sigs = intent.get("signals") or []
    sig_rows = "".join(
        f'<div class="sig"><span class="pts">+{s["points"]}</span><span class="lb">{_esc(s["label"])}</span></div>'
        for s in intent_sigs
    ) or '<div class="sig"><span class="lb muted">No buying signals detected yet.</span></div>'
    intent_html = f"""
    <section>
      <h3>Buying intent</h3>
      <div class="intent {intent_level}" style="--deg:{intent_deg}deg">
        <div class="gauge"><span class="val">{intent_score}</span><span class="of">/ 100</span></div>
        <div class="meta">
          <span class="lvl"><span class="kd"></span>{_esc(intent_level)}</span>
          <div class="sm">{_esc(intent_sm)}</div>
        </div>
      </div>
      <div style="margin-top:12px">{sig_rows}</div>
    </section>""" if intent else ""

    # ---- richer sections (only render when data present) ----
    def _sec(title, inner):
        return f'<section><h3>{title}</h3>{inner}</section>' if inner else ""

    snapshot = brain.get("snapshot", "")
    snapshot_html = _sec("Company snapshot", f'<div class="why">{_esc(snapshot)}</div>') if snapshot and snapshot != "unknown" else ""

    pains = [p for p in (brain.get("pain_points") or []) if p and p != "unknown"]
    pains_html = _sec("Likely pain points", _list_html(pains)) if pains else ""

    opener = brain.get("opener", "")
    opener_html = _sec("Personalized opener", f'<div class="opener">{_esc(opener)}</div>') if opener and opener != "unknown" else ""

    dqs = [q for q in (brain.get("discovery_questions") or []) if q and q != "unknown"]
    dq_html = ""
    if dqs:
        rows = "".join(f'<div class="dq"><span class="qn">{i+1}</span><span>{_esc(q)}</span></div>' for i, q in enumerate(dqs))
        dq_html = _sec("Discovery questions", f'<div class="dqs">{rows}</div>')

    objs = [o for o in (brain.get("objections") or []) if isinstance(o, dict) and o.get("objection")]
    obj_html = ""
    if objs:
        rows = "".join(
            f'<div class="obj"><div class="o">{_esc(o.get("objection",""))}</div>'
            f'<div class="r">{_esc(o.get("response",""))}</div></div>' for o in objs)
        obj_html = _sec("Objection prep", f'<div class="objs">{rows}</div>')

    # buying committee now supports [{role, why}] or plain strings
    comm = brain.get("buying_committee") or []
    comm_rows = ""
    for c in comm:
        if isinstance(c, dict):
            comm_rows += f'<div class="cm"><b>{_esc(c.get("role","?"))}</b><span>{_esc(c.get("why",""))}</span></div>'
        else:
            comm_rows += f'<div class="cm"><b>{_esc(c)}</b></div>'
    comm_html = _sec("Buying committee", f'<div class="cms">{comm_rows}</div>') if comm_rows else ""

    comp = brain.get("competitor_angle", "")
    comp_html = _sec("Competitor angle", f'<div class="why">{_esc(comp)}</div>') if comp and comp != "unknown" else ""

    channel = brain.get("best_channel", "")
    nexta = brain.get("next_action", "")
    play_html = ""
    if (channel and channel != "unknown") or (nexta and nexta != "unknown"):
        play_html = _sec("Play", (
            (f'<div class="kv"><span class="k">Best channel</span><span>{_esc(channel)}</span></div>' if channel and channel != "unknown" else "") +
            (f'<div class="kv"><span class="k">Next action</span><span>{_esc(nexta)}</span></div>' if nexta and nexta != "unknown" else "")
        ))

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(company)} - Account Brief</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; }}
  :root {{
    --bg:#08080A; --panel:#131318; --panel-2:#17171E; --panel-hi:#1D1D26;
    --line:#232330; --line-2:#2E2E3D;
    --text:#F4F4F6; --text-2:#A6A6B4; --text-3:#6B6B7B;
    --accent:#F0603A; --accent-2:#FF7E5B; --accent-glow:rgba(240,96,58,.5);
    --cyan:#2DD4BF; --violet:#8B7CF6;
    --green:#34D399; --amber:#FBBF48; --red:#F87171;
  }}
  body {{ margin:0; background:var(--bg); color:var(--text); line-height:1.6;
    font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;
    -webkit-font-smoothing:antialiased; letter-spacing:-0.008em; }}
  .sheet {{ max-width:840px; margin:24px auto; background:var(--panel);
    border:1px solid var(--line); border-radius:18px; overflow:hidden; }}

  /* header */
  .top {{ padding:28px 32px; position:relative; border-bottom:1px solid var(--line);
    background:
      radial-gradient(500px 200px at 85% -20%, rgba(240,96,58,.16), transparent 60%),
      linear-gradient(180deg, var(--panel-2), var(--panel)); }}
  .top .eyebrow {{ font-size:11px; letter-spacing:.12em; text-transform:uppercase;
    color:var(--accent); font-weight:600; margin:0 0 18px;
    display:inline-flex; align-items:center; gap:7px; }}
  .top .eyebrow .d {{ width:5px; height:5px; border-radius:50%; background:var(--accent);
    box-shadow:0 0 8px var(--accent-glow); }}
  .headrow {{ display:flex; align-items:center; gap:16px; }}
  .avatar {{ width:56px; height:56px; flex-shrink:0; border-radius:15px;
    background:linear-gradient(145deg, var(--accent-2), var(--accent));
    display:grid; place-items:center; font-size:21px; font-weight:700; color:#fff;
    box-shadow:0 0 0 1px rgba(255,255,255,.1), 0 6px 22px -6px var(--accent-glow); }}
  .top h1 {{ margin:0; font-size:29px; font-weight:600; letter-spacing:-0.025em; line-height:1.06; }}
  .top .by {{ font-size:13px; color:var(--text-2); margin-top:4px; }}
  .row {{ display:flex; gap:8px; flex-wrap:wrap; margin-top:20px; }}
  .pill {{ font-size:12px; font-weight:600; background:var(--panel-hi);
    color:var(--text-2); padding:6px 12px; border-radius:100px; border:1px solid var(--line-2);
    display:inline-flex; align-items:center; gap:6px; }}
  .pill.tech {{ background:rgba(139,124,246,.14); color:var(--violet); border-color:transparent; }}
  .pill.hi {{ background:rgba(52,211,153,.14); color:var(--green); border-color:transparent; }}
  .pill.mid {{ background:rgba(251,191,72,.14); color:var(--amber); border-color:transparent; }}
  .pill.lo {{ background:rgba(248,113,113,.14); color:var(--red); border-color:transparent; }}
  .pill .kd {{ width:6px; height:6px; border-radius:50%; background:currentColor; }}

  .body {{ padding:28px 32px; }}
  section {{ margin-bottom:26px; }}
  section:last-child {{ margin-bottom:0; }}
  h3 {{ font-size:11.5px; margin:0 0 12px; color:var(--text-3); font-weight:600;
    text-transform:uppercase; letter-spacing:.09em;
    display:flex; align-items:center; gap:12px; }}
  h3::after {{ content:""; flex:1; height:1px; background:var(--line); }}
  h4 {{ margin:0 0 5px; font-size:11.5px; color:var(--accent); text-transform:uppercase;
    letter-spacing:.05em; font-weight:600; }}
  p {{ margin:0; }}
  ul {{ margin:0; padding-left:0; list-style:none; }}
  ul li {{ position:relative; padding-left:20px; margin-bottom:8px; font-size:14.5px; color:var(--text); }}
  ul li::before {{ content:""; position:absolute; left:2px; top:9px; width:6px; height:6px;
    border-radius:50%; background:var(--accent); }}
  a {{ color:var(--cyan); font-size:11px; margin-left:8px; text-decoration:none; font-weight:500; }}
  a:hover {{ text-decoration:underline; }}
  .muted {{ color:var(--text-3); }}

  .angle {{ background:rgba(240,96,58,.08); border:1px solid rgba(240,96,58,.28);
    border-radius:13px; padding:16px 18px; font-size:15.5px; font-weight:500; color:var(--text);
    display:flex; gap:13px; }}
  .angle .q {{ color:var(--accent); flex-shrink:0; font-size:26px; line-height:.9;
    font-weight:700; }}

  .why {{ font-size:15px; color:var(--text); background:var(--panel-2);
    border:1px solid var(--line); border-radius:12px; padding:15px 17px; }}

  .trigs {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; }}
  @media(max-width:600px){{ .trigs {{ grid-template-columns:1fr; }} }}
  .trig {{ background:var(--panel-2); border:1px solid var(--line); border-radius:12px; padding:13px 15px; }}
  .trig ul li {{ font-size:13px; padding-left:16px; }}
  .trig ul li::before {{ width:5px; height:5px; top:8px; }}

  .committee {{ display:flex; flex-wrap:wrap; gap:8px; }}
  .committee span {{ font-size:13px; font-weight:500; background:var(--panel-2);
    border:1px solid var(--line-2); border-radius:100px; padding:6px 13px; color:var(--text-2); }}

  .avoid {{ font-size:14.5px; color:var(--text); background:rgba(248,113,113,.07);
    border:1px solid rgba(248,113,113,.25); border-radius:12px; padding:14px 16px;
    display:flex; gap:11px; align-items:flex-start; }}
  .avoid svg {{ width:17px; height:17px; color:var(--red); flex-shrink:0; margin-top:2px; }}

  .email {{ background:var(--panel-2); border:1px solid var(--line); border-radius:13px; overflow:hidden; }}
  .email .subj {{ font-weight:600; padding:13px 16px; border-bottom:1px solid var(--line); font-size:14px; }}
  .email .subj span {{ color:var(--text-3); font-weight:500; margin-right:6px;
    text-transform:uppercase; font-size:11px; letter-spacing:.05em;
    font-family:'JetBrains Mono',monospace; }}
  .email .msg {{ padding:16px; white-space:pre-wrap; font-size:14px; color:var(--text-2); line-height:1.7; }}
  .email .src {{ padding:10px 16px; border-top:1px solid var(--line); font-size:11px; color:var(--text-3); }}

  .foot {{ padding:15px 32px; background:var(--panel-2); border-top:1px solid var(--line);
    font-size:12px; color:var(--text-3); display:flex; justify-content:space-between;
    flex-wrap:wrap; gap:6px; align-items:center; }}
  .foot .g {{ display:inline-flex; align-items:center; gap:6px; }}
  .foot .g svg {{ width:13px; height:13px; color:var(--cyan); }}

  /* intent score */
  .intent {{ display:flex; gap:18px; align-items:center; background:var(--panel-2);
    border:1px solid var(--line); border-radius:14px; padding:18px 20px; }}
  .intent .gauge {{ width:74px; height:74px; flex-shrink:0; border-radius:50%;
    display:grid; place-items:center; position:relative; }}
  .intent .gauge .val {{ font-size:23px; font-weight:700; line-height:1; }}
  .intent .gauge .of {{ font-size:9px; color:var(--text-3); margin-top:1px; }}
  .intent .meta {{ flex:1; min-width:0; }}
  .intent .lvl {{ font-size:12px; font-weight:700; text-transform:uppercase;
    letter-spacing:.06em; display:inline-flex; align-items:center; gap:6px;
    padding:4px 11px; border-radius:100px; margin-bottom:7px; }}
  .intent .lvl .kd {{ width:6px; height:6px; border-radius:50%; background:currentColor; }}
  .intent .sm {{ font-size:14px; color:var(--text); }}
  .intent.hot .gauge {{ background:conic-gradient(var(--accent) var(--deg), var(--panel-hi) 0); }}
  .intent.warm .gauge {{ background:conic-gradient(var(--amber) var(--deg), var(--panel-hi) 0); }}
  .intent.cool .gauge {{ background:conic-gradient(var(--violet) var(--deg), var(--panel-hi) 0); }}
  .intent.cold .gauge {{ background:conic-gradient(var(--text-3) var(--deg), var(--panel-hi) 0); }}
  .intent .gauge::before {{ content:""; position:absolute; inset:7px; border-radius:50%;
    background:var(--panel-2); }}
  .intent .gauge .val, .intent .gauge .of {{ position:relative; z-index:1; }}
  .intent.hot .lvl {{ background:rgba(240,96,58,.14); color:var(--accent); }}
  .intent.warm .lvl {{ background:rgba(251,191,72,.14); color:var(--amber); }}
  .intent.cool .lvl {{ background:rgba(139,124,246,.14); color:var(--violet); }}
  .intent.cold .lvl {{ background:var(--panel-hi); color:var(--text-3); }}
  .sig {{ display:flex; align-items:center; gap:10px; font-size:13px; padding:7px 0;
    border-bottom:1px solid var(--line); }}
  .sig:last-child {{ border-bottom:none; }}
  .sig .pts {{ font-family:'JetBrains Mono',monospace; font-size:12px; font-weight:600;
    color:var(--cyan); flex-shrink:0; width:38px; }}
  .sig .lb {{ flex:1; color:var(--text-2); }}

  /* opener */
  .opener {{ background:rgba(45,212,191,.07); border:1px solid rgba(45,212,191,.28);
    border-radius:12px; padding:15px 17px; font-size:15px; font-weight:500; color:var(--text);
    font-style:italic; }}
  /* discovery questions */
  .dqs {{ display:flex; flex-direction:column; gap:8px; }}
  .dq {{ display:flex; gap:12px; align-items:flex-start; font-size:14px; }}
  .dq .qn {{ flex-shrink:0; width:22px; height:22px; border-radius:7px; background:var(--panel-hi);
    border:1px solid var(--line-2); display:grid; place-items:center; font-size:11px;
    font-weight:700; color:var(--accent); font-family:'JetBrains Mono',monospace; }}
  /* objections */
  .objs {{ display:flex; flex-direction:column; gap:10px; }}
  .obj {{ border:1px solid var(--line); border-radius:11px; overflow:hidden; }}
  .obj .o {{ padding:10px 14px; font-size:13.5px; font-weight:600; background:var(--panel-hi);
    color:var(--text); }}
  .obj .o::before {{ content:"“"; color:var(--text-3); margin-right:2px; }}
  .obj .r {{ padding:10px 14px; font-size:13.5px; color:var(--text-2); }}
  .obj .r::before {{ content:"→ "; color:var(--cyan); font-weight:700; }}
  /* committee */
  .cms {{ display:grid; grid-template-columns:1fr 1fr; gap:8px; }}
  @media(max-width:600px){{ .cms {{ grid-template-columns:1fr; }} }}
  .cm {{ background:var(--panel-2); border:1px solid var(--line); border-radius:10px;
    padding:11px 13px; }}
  .cm b {{ display:block; font-size:13.5px; color:var(--text); }}
  .cm span {{ font-size:12px; color:var(--text-3); }}
  /* play (key-value) */
  .kv {{ display:flex; gap:14px; padding:9px 0; border-bottom:1px solid var(--line); font-size:14px; }}
  .kv:last-child {{ border-bottom:none; }}
  .kv .k {{ flex-shrink:0; width:100px; color:var(--accent); font-weight:600; font-size:12px;
    text-transform:uppercase; letter-spacing:.04em; padding-top:1px; }}
  .kv span:last-child {{ color:var(--text); }}
</style></head>
<body>
<div class="sheet">
  <div class="top">
    <p class="eyebrow"><span class="d"></span> Synapse · Account Brief · for {_esc(sender)}</p>
    <div class="headrow">
      <div class="avatar">{_esc(initials)}</div>
      <div>
        <h1>{_esc(company)}</h1>
        <div class="by">{_esc(tech_res.get('title','') or 'Company research')}</div>
      </div>
    </div>
    <div class="row">
      <span class="pill {fit_kind}"><span class="kd"></span>{_esc(fit_label)}</span>
      {_pill('Confidence: ' + str(conf))}
      {_pill('Lead: ' + str(brain.get('recommended_service','-')))}
      {'<span class="pill">AI</span>' if ai_flag else '<span class="pill">Rule-based</span>'}
    </div>
  </div>
  <div class="body">
    {intent_html}
    {snapshot_html}
    <section>
      <h3>Why this account</h3>
      <div class="why">{_esc(brain.get('fit_reason','-'))}</div>
    </section>

    <section>
      <h3>Pitch angle</h3>
      <div class="angle"><span class="q">&#8220;</span><div>{_esc(brain.get('pitch_angle','-'))}</div></div>
    </section>

    {opener_html}
    {pains_html}

    <section>
      <h3>Talking points</h3>
      {_list_html(brain.get('talking_points'))}
    </section>

    {dq_html}
    {obj_html}

    <section>
      <h3>Trigger events · with source</h3>
      {_trigger_html(triggers)}
    </section>

    <section>
      <h3>Tech stack</h3>
      <div class="row" style="margin-top:0">{_tech_html(tech_res)}</div>
    </section>

    {comm_html}
    {comp_html}
    {play_html}

    <section>
      <h3>What to avoid</h3>
      <div class="avoid"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 8v4M12 16h.01"/></svg><div>{_esc(brain.get('what_to_avoid','-'))}</div></div>
    </section>

    <section>
      <h3>Ready-to-send email</h3>
      <div class="email">
        <div class="subj"><span>Subject</span>{_esc(email.get('subject',''))}</div>
        <div class="msg">{_esc(email.get('body',''))}</div>
        {'<div class="src">Hook source: <a href="' + _esc(src) + '" target="_blank">' + _esc(src) + '</a></div>' if src else ''}
      </div>
    </section>

  </div>
  <div class="foot">
    <span class="g"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3 4 6v6c0 5 3.5 7.5 8 9 4.5-1.5 8-4 8-9V6l-8-3z"/><path d="m9 12 2 2 4-4"/></svg>Every claim carries a source</span>
    <span>Generated by Synapse Research Agent</span>
  </div>
</div>
</body></html>"""


def save(html_str: str, company: str, out_dir: str = "briefs") -> str:
    """Brief ko file mein likho, path lautao."""
    Path(out_dir).mkdir(exist_ok=True)
    safe = "".join(c if c.isalnum() else "_" for c in company).strip("_") or "brief"
    path = Path(out_dir) / f"{safe}.html"
    path.write_text(html_str, encoding="utf-8")
    return str(path)


if __name__ == "__main__":
    pb = json.loads(open("playbook.json", encoding="utf-8").read())
    triggers = {"hiring": [{"title": "Acme hiring 20 engineers", "link": "http://example.com/jobs"}]}
    tech = {"tech": [{"name": "WordPress", "category": "CMS"}], "title": "Acme Corp"}
    brain = {"fit_score": "medium", "fit_reason": "Hiring signal + digital presence.",
             "recommended_service": "AI Tool Automation",
             "pitch_angle": "Hiring dikhi - automation ka mauka.",
             "talking_points": ["Hiring signal", "AI saves time"],
             "buying_committee": ["Founder", "Marketing head"],
             "what_to_avoid": "Teeno service mat thooso.", "confidence": "low", "_fallback": True}
    email = {"subject": "Acme - quick idea", "body": "Hi Acme team,\n...", "source": "http://example.com/jobs"}
    out = build("Acme Corp", pb, triggers, tech, brain, email)
    path = save(out, "Acme Corp")
    print("Brief saved:", path)
