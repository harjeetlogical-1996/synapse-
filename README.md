# Synapse — Research Agent (Phase 1, v0.1)

Sales team ke liye AI research assistant. Company ka naam do → 30 second mein
ek account brief (trigger events + tech stack + pitch angle + ready email).

Ye Synapse ka pehla agent hai (Stage 1: Lead Gen). Digitograffi ke liye tuned.

## Kaise chalao

```bash
cd synapse
python run.py "Company Name" "company.com"
```

Output: `briefs/Company_Name.html` — browser mein khud khul jaayega.

Bina arguments ke: `python run.py` → playbook ke test_account ko use karega,
ya poochega.

## Setup (keys ke saath full power)

Tool bina keys ke bhi chalta hai (rule-based brief), par keys se bahut behtar:

1. `.env.example` ko copy karke `.env` banao
2. Do keys bharo:
   - **SERPER_API_KEY** — [serper.dev](https://serper.dev) (free 2,500 search) — trigger events ke liye
   - **ANTHROPIC_API_KEY** — [console.anthropic.com](https://console.anthropic.com) — smart brief + email ke liye

Bas. Dobara `python run.py ...` chalao — ab funding/hiring/news bhi aayenge aur
brief Claude se banega.

## Files (6 module)

| File | Kaam |
|------|------|
| `playbook.json` | **Digitograffi ki info** — kya bechte, kise. Isse har brief smart banta. |
| `search.py` | Trigger events (funding/hiring/news) — Serper |
| `techstack.py` | Website scan → tech stack (free) |
| `brain.py` | AI — pitch angle, talking points (Claude) |
| `emailwriter.py` | Personalized outreach email |
| `brief.py` | Sab jodkr 1-page HTML brief |
| `run.py` | Sab chalane wala main runner |
| `config.py` | API keys + settings |

## Guardrail

Har claim ke peeche **source** hota hai. Tool koi jhootha fact nahi banata —
jo online mila wahi use karta hai, warna "unknown" bolta hai.

## Playbook badalna

Partner ki asli info aate hi `playbook.json` update karo (company, services,
ideal customer, test_account). Poora tool usi hisaab se behave karega — code
nahi chhoona.
