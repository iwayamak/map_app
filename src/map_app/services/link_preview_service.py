import hashlib
import re
import ssl
import threading
from html import unescape
from urllib.error import URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from django.core.cache import cache


LINK_PREVIEW_CACHE_TIMEOUT_SECONDS = 60 * 60 * 24
LINK_PREVIEW_FAILURE_CACHE_TIMEOUT_SECONDS = 60 * 10
LINK_PREVIEW_REQUEST_TIMEOUT_SECONDS = 2
LINK_PREVIEW_MAX_URLS = 5

URL_PATTERN = re.compile(r"(https?://[^\s<]+)")
TITLE_TAG_PATTERN = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
CHARSET_PATTERN = re.compile(
    rb"<meta[^>]+charset=[\"']?([a-zA-Z0-9_\-]+)",
    re.IGNORECASE,
)
ICON_LINK_PATTERN = re.compile(
    r"<link[^>]+(?:rel=[\"'][^\"']*(?:icon|shortcut icon|apple-touch-icon)[^\"']*[\"'])[^>]+href=[\"'](.*?)[\"']",
    re.IGNORECASE | re.DOTALL,
)
OG_TITLE_PATTERN = re.compile(
    r"<meta[^>]+property=[\"']og:title[\"'][^>]+content=[\"'](.*?)[\"']",
    re.IGNORECASE | re.DOTALL,
)


def split_trailing_url_punctuation(value):
    text = str(value or "")
    trailing = ""
    while text and re.search(r"[),.!?]$", text):
        trailing = text[-1] + trailing
        text = text[:-1]
    return text, trailing


def extract_urls(text):
    urls = []
    seen = set()
    for match in URL_PATTERN.finditer(str(text or "")):
        raw_url = match.group(1)
        url, _ = split_trailing_url_punctuation(raw_url)
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            continue
        if url in seen:
            continue
        seen.add(url)
        urls.append(url)
        if len(urls) >= LINK_PREVIEW_MAX_URLS:
            break
    return urls


def normalize_title(value):
    title = re.sub(r"\s+", " ", unescape(str(value or ""))).strip()
    if len(title) > 120:
        return title[:117] + "..."
    return title


def extract_title_from_html(html):
    if not html:
        return None
    og_match = OG_TITLE_PATTERN.search(html)
    if og_match:
        title = normalize_title(og_match.group(1))
        if title:
            return title
    title_match = TITLE_TAG_PATTERN.search(html)
    if title_match:
        title = normalize_title(title_match.group(1))
        if title:
            return title
    return None


def extract_favicon_url_from_html(url, html):
    if not html:
        return _build_default_favicon_url(url)

    icon_match = ICON_LINK_PATTERN.search(html)
    if icon_match:
        href = (icon_match.group(1) or "").strip()
        if href:
            return urljoin(url, href)
    return _build_default_favicon_url(url)


def decode_html_bytes(content, charset=None):
    candidates = []
    if charset:
        candidates.append(charset)

    meta_match = CHARSET_PATTERN.search(content or b"")
    if meta_match:
        meta_charset = meta_match.group(1).decode("ascii", errors="ignore")
        if meta_charset and meta_charset not in candidates:
            candidates.append(meta_charset)

    for fallback in ("utf-8", "cp932", "shift_jis", "euc_jp", "iso2022_jp", "latin-1"):
        if fallback not in candidates:
            candidates.append(fallback)

    for candidate in candidates:
        try:
            return content.decode(candidate)
        except (LookupError, UnicodeDecodeError):
            continue
    return content.decode("utf-8", errors="ignore")


def _build_cache_key(url):
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return f"link_preview_meta:{digest}"


def _build_default_favicon_url(url):
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return ""
    return f"{parsed.scheme}://{parsed.netloc}/favicon.ico"


def fetch_link_preview(url, *, urlopen_func=urlopen, cache_backend=cache):
    cache_key = _build_cache_key(url)
    cached = cache_backend.get(cache_key)
    if cached is not None:
        return cached or None

    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; MapApp/1.0)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )

    try:
        with urlopen_func(request, timeout=LINK_PREVIEW_REQUEST_TIMEOUT_SECONDS) as response:
            content_type = response.headers.get_content_type()
            if content_type and "html" not in content_type:
                cache_backend.set(cache_key, "", LINK_PREVIEW_FAILURE_CACHE_TIMEOUT_SECONDS)
                return None
            charset = response.headers.get_content_charset() or "utf-8"
            html = decode_html_bytes(response.read(65536), charset=charset)
    except URLError as error:
        reason = getattr(error, "reason", None)
        if not isinstance(reason, ssl.SSLCertVerificationError):
            cache_backend.set(cache_key, "", LINK_PREVIEW_FAILURE_CACHE_TIMEOUT_SECONDS)
            return None
        try:
            insecure_context = ssl._create_unverified_context()
            with urlopen_func(request, timeout=LINK_PREVIEW_REQUEST_TIMEOUT_SECONDS, context=insecure_context) as response:
                content_type = response.headers.get_content_type()
                if content_type and "html" not in content_type:
                    cache_backend.set(cache_key, "", LINK_PREVIEW_FAILURE_CACHE_TIMEOUT_SECONDS)
                    return None
                charset = response.headers.get_content_charset() or "utf-8"
                html = decode_html_bytes(response.read(65536), charset=charset)
        except (OSError, URLError, ValueError):
            cache_backend.set(cache_key, "", LINK_PREVIEW_FAILURE_CACHE_TIMEOUT_SECONDS)
            return None
    except (OSError, URLError, ValueError):
        cache_backend.set(cache_key, "", LINK_PREVIEW_FAILURE_CACHE_TIMEOUT_SECONDS)
        return None

    preview = {
        "title": extract_title_from_html(html) or "",
        "favicon_url": extract_favicon_url_from_html(url, html) or "",
    }
    has_useful_preview = bool(preview["title"] or preview["favicon_url"])
    cache_backend.set(
        cache_key,
        preview if has_useful_preview else "",
        LINK_PREVIEW_CACHE_TIMEOUT_SECONDS if has_useful_preview else LINK_PREVIEW_FAILURE_CACHE_TIMEOUT_SECONDS,
    )
    return preview if has_useful_preview else None


def build_link_preview_map(text, *, fetch_link_preview_func=fetch_link_preview):
    preview_map = {}
    for url in extract_urls(text):
        preview = fetch_link_preview_func(url)
        if preview:
            preview_map[url] = preview
    return preview_map


def warm_link_preview_cache(text, *, build_link_preview_map_func=build_link_preview_map):
    if not extract_urls(text):
        return
    build_link_preview_map_func(text)


def schedule_link_preview_cache_warmup(text, *, warm_link_preview_cache_func=warm_link_preview_cache):
    if not extract_urls(text):
        return
    threading.Thread(target=warm_link_preview_cache_func, args=(text,), daemon=True).start()
