from urllib.parse import parse_qs, unquote, urlparse
from ddgs import DDGS
from schemas import SearchFinding


def clean_url(raw_url: str) -> str:
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
        with DDGS(timeout=12) as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        for item in results:
            title = (item.get("title") or "").strip()
            url = clean_url(item.get("href") or "")
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
    except Exception:
        return []

    return findings



# def search_web(query: str, max_results: int = 5) -> list[SearchFinding]:
#     """Run a web search via DuckDuckGo and return structured findings"""
#     findings: list[SearchFinding] = []

#     try:
#         with DDGS() as ddgs:
#             results = list(ddgs.text(query, max_results=max_results))
#         for item in results:
#             title = (item.get("title") or "").strip()
#             url = (item.get("href") or "").strip()
#             snippet = (item.get("body") or "").strip()
#             if title or snippet:
#                 findings.append(
#                     SearchFinding(
#                         title=title or "Untitled Result",
#                         url=url or "No URL provided",
#                         snippet=snippet or "No snippet available",
#                         source_type="web_search",
#                     )
#                 )
#     except Exception as e:
#         findings.append(
#             SearchFinding(
#                 title="Web Search Fallback Notice",
#                 url="local://sample-fallback",
#                 snippet=(
#                     f"Sample fallback data used because live search encountered an issue ({e})."
#                     f"Topic queried: '{query}'. Real-time market figures may be incomplete."
#                 ),
#                 source_type="sample_fallback",
#             )
#         )
#         return findings

#     if not findings:
#         findings.append(
#             SearchFinding(
#                 title="Sample Fallback Record",
#                 url="local://sample-fallback",
#                 snippet=(
#                     f"Sample fallback data: no live search results were returned for '{query}'. "
#                     f"Treat downstream observations as provisional until verified with primary sources."
#                 ),
#                 source_type="sample-fallback",
#             )
#         )    
#     return findings
