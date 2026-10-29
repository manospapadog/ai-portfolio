import requests
from bs4 import BeautifulSoup

# (label, url, a word that should appear on the real page)
CHECKS = [
    ("Gong release notes", "https://help.gong.io/docs/release-notes", "release"),
    ("Gong monthly updates", "https://help.gong.io/docs/en/our-monthly-updates", "release"),
    ("Gong press", "https://www.gong.io/press", "gong"),
    ("Clari product updates", "https://community.clari.com/product-updates", "release"),
    ("Salesloft release notes", "https://champions.salesloft.com/product-updates", "release"),
    ("Salesloft newsroom", "https://www.salesloft.com/company/newsroom", "salesloft"),
    ("Aviso press", "https://www.aviso.com/press", "aviso"),
    ("Aviso blog", "https://www.aviso.com/blog", "aviso"),
    ("Terret homepage", "https://terret.ai", "terret"),
    ("Backstory homepage", "https://www.backstory.ai", "backstory"),
]

HEADERS = {"User-Agent": "Mozilla/5.0 (personal portfolio project; weekly check)"}

for label, url, keyword in CHECKS:
    print(f"\n=== {label} ===")
    print("URL:", url)
    try:
        r = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
    except Exception as e:
        print("RESULT: FAILED TO CONNECT:", e)
        continue

    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = " ".join(soup.get_text(" ").split())

    print("Status:", r.status_code)
    if r.url.rstrip("/") != url.rstrip("/"):
        print("Redirected to:", r.url)
    print("Visible text length:", len(text))
    print("Keyword found:", keyword.lower() in text.lower())
    print("Preview:", text[:200])

    if r.status_code != 200:
        print("RESULT: PROBLEM (blocked or not found)")
    elif len(text) < 1500:
        print("RESULT: PROBLEM (very little text, probably loads with JavaScript)")
    elif keyword.lower() not in text.lower():
        print("RESULT: CHECK (page loaded, but expected content missing)")
    else:
        print("RESULT: OK")