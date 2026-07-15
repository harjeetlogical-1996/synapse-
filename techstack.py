"""
Synapse Module 2 - TECH STACK (website scan).

Company ki website khud khol ke padhta hai aur detect karta hai kaunse tools
use karte hain (CRM, analytics, chat, ecommerce, page builders, hosting).
Isse pitch mein "maine dekha aap X use karte ho" wali asli baat aati hai.

FREE - koi API nahi, sirf website ka HTML padhta hai (stdlib urllib).
Website na khule to saaf note lautaata hai, crash nahi.
"""
import re
import ssl
import urllib.request
import urllib.error

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) synapse-tech/0.1"

# HTML mein ye signatures dhoondhte hain -> tool ka naam.
# Har entry: (regex pattern, "Tool Name", "category")
_SIGNATURES = [
    (r"wp-content|wp-includes",              "WordPress",        "CMS"),
    (r"/wp-json/",                           "WordPress",        "CMS"),
    (r"cdn\.shopify\.com|myshopify",         "Shopify",          "Ecommerce"),
    (r"wixstatic\.com|_wix",                 "Wix",              "Website builder"),
    (r"squarespace",                         "Squarespace",      "Website builder"),
    (r"webflow",                             "Webflow",          "Website builder"),
    (r"elementor",                           "Elementor",        "Page builder"),
    (r"hubspot|hs-scripts|hs-analytics",     "HubSpot",          "Marketing/CRM"),
    (r"salesforce|pardot",                   "Salesforce",       "CRM"),
    (r"marketo",                             "Marketo",          "Marketing"),
    (r"google-analytics|gtag\(|ga\.js",      "Google Analytics", "Analytics"),
    (r"googletagmanager",                    "Google Tag Mgr",   "Analytics"),
    (r"hotjar",                              "Hotjar",           "Analytics"),
    (r"segment\.com|segment\.io",            "Segment",          "Analytics"),
    (r"intercom",                            "Intercom",         "Chat/Support"),
    (r"drift\.com",                          "Drift",            "Chat/Support"),
    (r"zendesk",                             "Zendesk",          "Support"),
    (r"tawk\.to",                            "Tawk.to",          "Chat"),
    (r"cloudflare",                          "Cloudflare",       "Hosting/CDN"),
    (r"cdn\.jsdelivr|unpkg\.com",            "JS CDN",           "Frontend"),
    (r"react|__NEXT_DATA__|_next/",          "React/Next.js",    "Frontend"),
    (r"vue\.js|__vue__",                     "Vue.js",           "Frontend"),
    (r"mailchimp|list-manage",               "Mailchimp",        "Email marketing"),
    (r"calendly",                            "Calendly",         "Scheduling"),
    (r"stripe\.com|js\.stripe",              "Stripe",           "Payments"),
    (r"razorpay",                            "Razorpay",         "Payments"),
    (r"typeform",                            "Typeform",         "Forms"),
]

_RE_TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
_RE_DESC = re.compile(
    r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']', re.I)
_RE_GENERATOR = re.compile(
    r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)["\']', re.I)


def _normalize_url(site: str) -> str:
    site = (site or "").strip()
    if not site:
        return ""
    if not site.startswith(("http://", "https://")):
        site = "https://" + site
    return site


def _fetch(url: str) -> str:
    """Website ka HTML lao. Fail pe khali string."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE  # kuch sites ka SSL kharab hota hai
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            raw = resp.read(400_000)  # pehle 400KB kaafi hai
            charset = resp.headers.get_content_charset() or "utf-8"
            return raw.decode(charset, errors="ignore")
    except Exception:
        return ""


def detect(site: str) -> dict:
    """
    Website scan karke tech stack + basic info nikaalo.

    Returns:
        {
          "ok": bool,
          "note": str,
          "url": str,
          "title": str,
          "description": str,
          "tech": [ {"name":..., "category":...}, ... ],
        }
    """
    url = _normalize_url(site)
    if not url:
        return {"ok": False, "note": "Website URL is empty.", "url": "",
                "title": "", "description": "", "tech": []}

    html = _fetch(url)
    if not html:
        return {"ok": False, "note": f"Website did not open ({url}).", "url": url,
                "title": "", "description": "", "tech": []}

    title = ""
    m = _RE_TITLE.search(html)
    if m:
        title = re.sub(r"\s+", " ", m.group(1)).strip()[:200]

    description = ""
    m = _RE_DESC.search(html)
    if m:
        description = m.group(1).strip()[:300]

    # tech detect (duplicate hataake)
    found = {}
    for pattern, name, category in _SIGNATURES:
        if re.search(pattern, html, re.I):
            found[name] = category
    generator = ""
    m = _RE_GENERATOR.search(html)
    if m:
        generator = m.group(1).strip()

    tech = [{"name": n, "category": c} for n, c in found.items()]

    note = f"{len(tech)} tools detected." if tech else "No clear tech signal found."
    return {
        "ok": True, "note": note, "url": url,
        "title": title, "description": description,
        "generator": generator, "tech": tech,
    }


# Akela test:  python techstack.py example.com
if __name__ == "__main__":
    import sys
    site = sys.argv[1] if len(sys.argv) > 1 else "wordpress.org"
    print(f"Scanning: {site}\n")
    res = detect(site)
    print("OK:", res["ok"], "|", res["note"])
    print("URL:", res["url"])
    print("Title:", res["title"])
    print("Desc:", res["description"][:120])
    print("\nTech stack:")
    for t in res["tech"]:
        print(f"  - {t['name']}  ({t['category']})")
    if not res["tech"]:
        print("  (kuch nahi mila)")
