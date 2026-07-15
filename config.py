"""
Synapse config - API keys aur settings ek jagah.

Keys .env file se aati hain (jo git mein commit nahi hoti). Agar key nahi hai
to tool crash nahi karta - wo hissa skip ho jaata hai aur "key nahi mili" bolta.

.env example (synapse/.env banao):
    SERPER_API_KEY=your_serper_key
    GEMINI_API_KEY=your_gemini_key
"""
import os
from pathlib import Path

# .env ko manually padho (koi extra library nahi chahiye)
_ENV_PATH = Path(__file__).parent / ".env"


def _load_env():
    if not _ENV_PATH.exists():
        return
    for line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        # env mein pehle se hai to overwrite mat karo
        os.environ.setdefault(key, val)


_load_env()

SERPER_API_KEY = os.environ.get("SERPER_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Gemini model - flash-lite is the cheapest and always points to the latest.
# Cheaper -> pricier: gemini-flash-lite-latest, gemini-2.5-flash, gemini-flash-latest
GEMINI_MODEL = os.environ.get("SYNAPSE_GEMINI_MODEL", "gemini-flash-lite-latest")

# Kitne search results dekhne hain per query
SEARCH_RESULTS = 8

# Country/language for search
SEARCH_GL = "in"   # India; US ke liye "us"
SEARCH_HL = "en"


def have_serper() -> bool:
    return bool(SERPER_API_KEY)


def have_gemini() -> bool:
    return bool(GEMINI_API_KEY)
