# Every page the agent watches. Add or remove entries here.
#
# kind "page_text": save the visible text of the page (for text diffs)
# kind "links":     save the list of article links found on the page
# kind "sitemap":   save the list of URLs in an XML sitemap

SOURCES = [
    {"id": "gong-release-notes", "company": "Gong", "kind": "page_text",
     "url": "https://help.gong.io/docs/release-notes"},
    {"id": "gong-monthly-updates", "company": "Gong", "kind": "page_text",
     "url": "https://help.gong.io/docs/en/our-monthly-updates"},
    {"id": "gong-press", "company": "Gong", "kind": "links",
     "url": "https://www.gong.io/press", "link_contains": ["/press/"]},
    {"id": "gong-press-sitemap", "company": "Gong", "kind": "sitemap",
     "url": "https://www.gong.io/sitemap.xml", "url_contains": "/press/"},

    {"id": "salesloft-release-notes", "company": "Salesloft", "kind": "links",
     "url": "https://community.salesloft.com/product-updates",
     "link_contains": ["release-notes", "feature-release"]},

    {"id": "aviso-press", "company": "Aviso", "kind": "links",
     "url": "https://www.aviso.com/press", "link_contains": ["/press/"]},
    {"id": "aviso-blog", "company": "Aviso", "kind": "links",
     "url": "https://www.aviso.com/blog", "link_contains": ["/blog/"]},

    {"id": "terret-home", "company": "Terret", "kind": "page_text",
     "url": "https://www.terret.ai/"},
    {"id": "terret-sitemap", "company": "Terret", "kind": "sitemap",
     "url": "https://www.terret.ai/sitemap.xml"},

    {"id": "backstory-home", "company": "Backstory", "kind": "page_text",
     "url": "https://www.backstory.ai"},
    {"id": "backstory-sitemap", "company": "Backstory", "kind": "sitemap",
     "url": "https://www.backstory.ai/sitemap.xml"},
]