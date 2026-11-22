import logging
from urllib.parse import parse_qs, unquote, urlparse

from ddgs import DDGS
from schemas import SearchFinding

logger = logging.getLogger(__name__)


def _clean_url(raw_url: str) -> str:
    """Unwrap Bing ad-redirect URLs into clean destination URLs when present."""
    url = raw_url.strip()
    if not url:
        return "No URL provided"

    parsed = urlparse(url)
    if "bing.com" in parsed.netloc and parsed.path.startswith("/aclick"):
        target = parse_qs(parsed.query).get("u", [])
        if target:
            decoded = unquote(target[0]).strip()
            if decoded.startswith(("http://", "https://")):
                return decoded

    return url


def search_web(query: str, max_results: int = 5) -> list[SearchFinding]:
    """Run a web search via DuckDuckGo and return structured findings."""
    findings: list[SearchFinding] = []

    try:
        with DDGS(timeout=10) as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        for item in results:
            title = (item.get("title") or "").strip()
            url = _clean_url(item.get("href") or "")
            snippet = (item.get("body") or "").strip()
            if title or snippet:
                findings.append(
                    SearchFinding(
                        title=title or "Untitled Result",
                        url=url,
                        snippet=snippet or "No snippet available",
                        source_type="web_search",
                    )
                )
    except Exception as exc:
        logger.warning("DuckDuckGo search failed for query '%s': %s", query, exc)
        return []

    return findings