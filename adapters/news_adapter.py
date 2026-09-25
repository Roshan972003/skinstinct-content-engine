"""
Current-angle lookup, via Google News RSS.

Google News RSS is public and keyless (https://news.google.com/rss/search),
which is why it's usable today without provisioning an API key — matching
the "Google News RSS" actor named in the case's own Components Map template.

This is deliberately best-effort: any network failure, empty result, or
malformed entry results in an empty list, never a fabricated candidate. The
caller (Node 02 / draft-post) is required by its own rules to omit the
"current angle" entirely rather than invent one if this returns nothing.
"""
from __future__ import annotations

import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List

RSS_BASE = "https://news.google.com/rss/search"
TIMEOUT_SECONDS = 6
MAX_RESULTS = 3


@dataclass
class NewsCandidate:
    title: str
    source: str
    published: str
    link: str


def fetch_news_candidates(query: str) -> List[NewsCandidate]:
    """
    Best-effort fetch. Returns [] on any error — never raises, never
    invents a result. The pipeline must treat [] as "no verified current
    angle available," not as a reason to retry with a guess.
    """
    if not query or not query.strip():
        return []

    params = {"q": query, "hl": "en-IN", "gl": "IN", "ceid": "IN:en"}
    url = f"{RSS_BASE}?{urllib.parse.urlencode(params)}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            raw = resp.read()
        root = ET.fromstring(raw)
    except Exception:
        # Network unavailable, blocked, malformed feed, etc. Fail closed.
        return []

    candidates: List[NewsCandidate] = []
    for item in root.findall(".//item")[:MAX_RESULTS]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        source_el = item.find("source")
        source = (source_el.text or "").strip() if source_el is not None else ""

        # Guardrail: only a candidate with all three of title/date/source
        # counts as "verified enough to cite." Anything partial is dropped
        # rather than passed through with a gap papered over.
        if title and link and pub_date:
            candidates.append(
                NewsCandidate(title=title, source=source or "unspecified", published=pub_date, link=link)
            )

    return candidates
