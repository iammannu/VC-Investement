"""
Website scraper using httpx + BeautifulSoup.
Falls back to playwright for JS-heavy sites.
"""
import re
import httpx
from bs4 import BeautifulSoup
import structlog

logger = structlog.get_logger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
TIMEOUT = 30
MAX_CONTENT_LENGTH = 500_000  # 500KB


def scrape_website(url: str, use_playwright: bool = False) -> tuple[str, list[str]]:
    """
    Returns (cleaned_text, found_urls).
    Tries httpx first, playwright if JS-heavy or fails.
    """
    try:
        text = _scrape_with_httpx(url)
        if len(text.strip()) < 200:
            raise ValueError("Too little content, trying playwright")
        return text, _extract_links(text, url)
    except Exception as e:
        logger.warning("httpx_scrape_failed", url=url, error=str(e))
        if use_playwright:
            text = _scrape_with_playwright(url)
            return text, _extract_links(text, url)
        return "", []


def _scrape_with_httpx(url: str) -> str:
    with httpx.Client(headers=HEADERS, timeout=TIMEOUT, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()
        content = response.text[:MAX_CONTENT_LENGTH]
    return _html_to_text(content)


def _scrape_with_playwright(url: str) -> str:
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=30000)
            content = page.content()
            browser.close()
        return _html_to_text(content)
    except Exception as e:
        logger.error("playwright_scrape_failed", url=url, error=str(e))
        return ""


def _html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")

    # Remove noise elements
    for tag in soup.find_all(["script", "style", "nav", "footer", "header", "noscript", "iframe"]):
        tag.decompose()

    # Get meaningful text from these tags
    meaningful_tags = soup.find_all(
        ["h1", "h2", "h3", "h4", "p", "li", "td", "th", "blockquote", "article", "section", "main"]
    )

    lines: list[str] = []
    for tag in meaningful_tags:
        text = tag.get_text(separator=" ", strip=True)
        if len(text) > 20:
            lines.append(text)

    return "\n\n".join(lines)


def _extract_links(text: str, base_url: str) -> list[str]:
    urls = re.findall(r"https?://[^\s\"'<>]+", text)
    # Filter to same domain
    from urllib.parse import urlparse
    base_domain = urlparse(base_url).netloc
    same_domain = [u for u in urls if urlparse(u).netloc == base_domain]
    return list(set(same_domain))[:20]
