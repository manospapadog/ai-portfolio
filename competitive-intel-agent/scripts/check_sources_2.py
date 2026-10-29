import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

HEADERS = {"User-Agent": "Mozilla/5.0 (personal portfolio project; weekly check)"}

# (label, url, words to look for in link text/address; None = show long link titles)
PAGES = [
    ("Salesloft community", "https://community.salesloft.com", ["release", "update", "what"]),
    ("Gong press", "https://www.gong.io/press", None),
    ("Salesloft newsroom", "https://www.salesloft.com/company/newsroom", None),
    ("Aviso press", "https://www.aviso.com/press", None),
    ("Aviso blog", "https://www.aviso.com/blog", None),
]

for label, url, words in PAGES:
    print(f"\n=== {label} ===")
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
    except Exception as e:
        print("FAILED:", e)
        continue
    soup = BeautifulSoup(r.content, "html.parser")
    seen, shown = set(), 0
    for a in soup.find_all("a", href=True):
        text = " ".join(a.get_text(" ").split())
        href = urljoin(r.url, a["href"])
        if href in seen:
            continue
        if words:
            match = any(w in (text + href).lower() for w in words)
        else:
            match = len(text) > 35
        if match:
            seen.add(href)
            print(f"  - {text[:90]} -> {href}")
            shown += 1
        if shown >= 15:
            break
    if shown == 0:
        print("  (no matching links in the static HTML)")

print("\n=== Feed / sitemap check ===")
BASES = ["https://www.gong.io", "https://www.salesloft.com", "https://www.aviso.com",
         "https://www.terret.ai", "https://www.backstory.ai"]
PATHS = ["/feed", "/rss", "/rss.xml", "/feed.xml", "/blog/feed", "/sitemap.xml"]
found = False
for base in BASES:
    for p in PATHS:
        try:
            r = requests.get(base + p, headers=HEADERS, timeout=15)
            ctype = r.headers.get("Content-Type", "")
            if r.status_code == 200 and ("xml" in ctype or r.text.lstrip().startswith("<?xml")):
                print("FOUND:", base + p, ctype)
                found = True
        except Exception:
            pass
if not found:
    print("None found.")