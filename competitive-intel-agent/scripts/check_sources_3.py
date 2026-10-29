import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

HEADERS = {"User-Agent": "Mozilla/5.0 (personal portfolio project; weekly check)"}

def get(url):
    return requests.get(url, headers=HEADERS, timeout=20)

print("=== Salesloft release notes page ===")
r = get("https://community.salesloft.com/product-updates")
soup = BeautifulSoup(r.content, "html.parser")
print("Status:", r.status_code)
n = 0
for a in soup.find_all("a", href=True):
    if "release-notes" in a["href"] or "feature-release" in a["href"]:
        print("  -", " ".join(a.get_text(' ').split())[:70], "->", urljoin(r.url, a["href"]))
        n += 1
        if n >= 10:
            break
if n == 0:
    print("  (no release-note links in static HTML)")

print("\n=== Salesloft newsroom (article links only) ===")
r = get("https://www.salesloft.com/company/newsroom")
soup = BeautifulSoup(r.content, "html.parser")
seen = set()
for a in soup.find_all("a", href=True):
    href = urljoin(r.url, a["href"])
    if "/company/newsroom/" in href and href not in seen:
        seen.add(href)
        print("  -", " ".join(a.get_text(' ').split())[:70], "->", href)
        if len(seen) >= 10:
            break
if not seen:
    print("  (no article links in static HTML)")

print("\n=== Gong sitemap: press pages with dates ===")
r = get("https://www.gong.io/sitemap.xml")
print("Status:", r.status_code, "| length:", len(r.text))
urls = re.findall(r"<loc>([^<]*/press/[^<]*)</loc>(?:\s*<lastmod>([^<]*)</lastmod>)?", r.text)
print("Press URLs in sitemap:", len(urls))
for u, d in urls[:5]:
    print("  -", d or "(no date)", u)