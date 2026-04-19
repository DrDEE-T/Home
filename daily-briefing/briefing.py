"""
briefing.py — DT Daily AI Briefing System
Run manually: python briefing.py
Run via cron:  0 7 * * * /path/to/venv/bin/python /path/to/briefing.py
"""

import base64
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import feedparser
from anthropic import Anthropic
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import config

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

load_dotenv()

LOG_FILE = Path("briefing.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
CREDENTIALS_FILE = Path("credentials.json")
TOKEN_FILE = Path("token.json")

# ---------------------------------------------------------------------------
# System prompt (verbatim from spec)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a research analyst for Dr. Denise Turley, an AI implementation practitioner and SVP of Technology, Data and AI at a national business association. She also teaches AI to professionals across healthcare, finance, legal, and nonprofit sectors. Her content authority is grounded in operational experience, not theory. Your job is to analyze each news item and produce a structured brief entry.

Follow these rules without exception.

RELEVANCE SCORING: Score each item against these three pillars. Drop any item that does not clearly connect to at least one. Do not force relevance.
Pillar 1. AI adoption failure: why implementations stall, the role of mindset, culture, and organizational commitment to change.
Pillar 2. Workforce anxiety and job impact: how AI is affecting jobs, skills, workplace behavior, and professional fears.
Pillar 3. AI governance inside real organizations: practical governance, responsible AI, compliance, and risk management in operations.

EXTRACTION RULE: Only assert what the source explicitly states. No inferred motivations. No assumed timelines. No general claims dressed as insights. If the source does not say it, you do not include it. This rule protects the credibility of a practitioner whose authority depends on accuracy.

OUTPUT FORMAT: For each relevant item produce exactly this structure and nothing else.

SOURCE: [publication name]
HEADLINE: [article headline]
PILLAR: [which of the three pillars this connects to — use exactly: Adoption failure, Workforce anxiety, or Governance]
WHAT IT SAYS: [one to two sentences. Only what the source explicitly states.]
DT'S TAKE: [Write a 3 to 4 sentence paragraph in DT's voice. She is a practitioner, not a commentator. She has sat in implementation rooms, watched pilots stall, and trained professionals in healthcare, finance, legal, and nonprofit organizations on what AI actually requires. This paragraph should carry that weight. It should say something specific and true that a LinkedIn audience of practitioners would not have heard from a generic AI newsletter. Ground every sentence in what the source says. Do not invent claims. Do not use hype language. Do not use em dashes. Write like someone who has been in the room, not someone covering it from the outside.]

If the item is not relevant to any pillar, respond with exactly: NOT_RELEVANT

Do not editorialize. Do not add context the source did not provide. Do not use hype language. Do not use em dashes. This output feeds directly into content that carries DT's professional credibility."""

# ---------------------------------------------------------------------------
# RSS collection
# ---------------------------------------------------------------------------

def _normalize_url(url: str) -> str:
    parsed = urlparse(url)
    return parsed.scheme + "://" + parsed.netloc + parsed.path.rstrip("/")


def _entry_timestamp(entry) -> Optional[datetime]:
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return None


def fetch_rss_feeds(feeds: list[str], is_primary: bool) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=config.LOOKBACK_HOURS)
    items = []
    for url in feeds:
        try:
            feed = feedparser.parse(url, request_headers={"User-Agent": "DTBriefingBot/1.0"})
            if feed.bozo and not feed.entries:
                log.warning("RSS parse issue for %s: %s", url, feed.bozo_exception)
                continue
            source_name = feed.feed.get("title", urlparse(url).netloc)
            for entry in feed.entries:
                ts = _entry_timestamp(entry)
                if ts and ts < cutoff:
                    continue
                link = entry.get("link", "")
                if not link:
                    continue
                summary = entry.get("summary", entry.get("description", ""))
                items.append(
                    {
                        "url": link,
                        "url_key": _normalize_url(link),
                        "title": entry.get("title", ""),
                        "source": source_name,
                        "content": _strip_html(summary),
                        "published": str(ts) if ts else "",
                        "is_primary": is_primary,
                        "origin": "rss",
                    }
                )
            log.info("RSS %s: %d items (primary=%s)", url, len(items), is_primary)
        except Exception as exc:
            log.error("RSS feed failed [%s]: %s", url, exc)
    return items


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text).strip()


# ---------------------------------------------------------------------------
# Web search via Anthropic
# ---------------------------------------------------------------------------

def run_web_searches(queries: list[str], client: Anthropic) -> list[dict]:
    items = []
    for query in queries:
        try:
            response = client.messages.create(
                model=config.ANTHROPIC_MODEL,
                max_tokens=1024,
                tools=[{"type": "web_search_20250305", "name": "web_search"}],
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f'Search for: "{query}"\n\n'
                            "Find the 3 to 5 most relevant news articles published in the "
                            "last 24 hours. Return ONLY a valid JSON array — no prose, no "
                            "markdown fences — using this schema:\n"
                            '[{"url":"...","title":"...","source_name":"...","summary":"..."}]'
                        ),
                    }
                ],
            )

            for block in response.content:
                if block.type == "text":
                    raw = block.text.strip()
                    extracted = _extract_json_array(raw)
                    if extracted is None:
                        log.warning("No parseable JSON from search query '%s'", query)
                        continue
                    for art in extracted:
                        url = art.get("url", "").strip()
                        if not url:
                            continue
                        items.append(
                            {
                                "url": url,
                                "url_key": _normalize_url(url),
                                "title": art.get("title", ""),
                                "source": art.get("source_name", "Web Search"),
                                "content": art.get("summary", ""),
                                "published": "",
                                "is_primary": True,
                                "origin": "search",
                                "search_query": query,
                            }
                        )
            log.info("Web search '%s': %d items found", query, len(items))
        except Exception as exc:
            log.error("Web search failed for query '%s': %s", query, exc)
        time.sleep(15)
    return items


def _extract_json_array(text: str) -> Optional[list]:
    try:
        start = text.index("[")
        end = text.rindex("]") + 1
        return json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError):
        return None


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def deduplicate(items: list[dict]) -> list[dict]:
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    unique = []
    for item in items:
        url_key = item.get("url_key", item.get("url", ""))
        title_key = _title_key(item.get("title", ""))
        if url_key in seen_urls or (title_key and title_key in seen_titles):
            continue
        seen_urls.add(url_key)
        if title_key:
            seen_titles.add(title_key)
        unique.append(item)
    log.info("Deduplication: %d -> %d items", len(items), len(unique))
    return unique


def _title_key(title: str) -> str:
    return re.sub(r"[^a-z0-9]", "", title.lower())[:60]


# ---------------------------------------------------------------------------
# Anthropic analysis — single batched call for all items
# ---------------------------------------------------------------------------

BATCH_SYSTEM_PROMPT = SYSTEM_PROMPT + """

You will receive multiple numbered news items. Analyze each against the three pillars.

Return ONLY a valid JSON array — no prose, no markdown fences. One object per item in order:
[
  {
    "item": 1,
    "relevant": true,
    "SOURCE": "publication name",
    "HEADLINE": "article headline",
    "PILLAR": "Adoption failure",
    "WHAT IT SAYS": "one to two sentences from the source only",
    "DT'S TAKE": "3 to 4 sentence paragraph in DT's practitioner voice"
  },
  {
    "item": 2,
    "relevant": false
  }
]

Use exactly one of these pillar values: Adoption failure, Workforce anxiety, Governance."""


def analyze_all_items(items: list[dict], client: Anthropic) -> list[dict]:
    if not items:
        return []

    numbered = ""
    for i, item in enumerate(items, 1):
        numbered += (
            f"ITEM {i}\n"
            f"Title: {item['title']}\n"
            f"Source: {item['source']}\n"
            f"Content: {item['content'][:600]}\n\n"
        )

    try:
        response = client.messages.create(
            model=config.ANALYSIS_MODEL,
            max_tokens=config.MAX_TOKENS,
            system=BATCH_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"Analyze these {len(items)} news items:\n\n{numbered}"}],
        )
        raw = response.content[0].text.strip()
        parsed = _extract_json_array(raw)
        if not parsed:
            log.error("Could not parse batch analysis JSON")
            return []

        results = []
        for entry in parsed:
            if not entry.get("relevant"):
                log.info("Not relevant: item %d", entry.get("item", "?"))
                continue
            idx = entry.get("item", 1) - 1
            source_item = items[idx] if 0 <= idx < len(items) else {}
            entry["is_primary"] = source_item.get("is_primary", True)
            pillar_raw = entry.get("PILLAR", "").lower()
            if "adoption" in pillar_raw:
                entry["pillar_group"] = "ADOPTION FAILURE"
            elif "workforce" in pillar_raw:
                entry["pillar_group"] = "WORKFORCE ANXIETY"
            elif "governance" in pillar_raw:
                entry["pillar_group"] = "GOVERNANCE"
            else:
                entry["pillar_group"] = "OTHER"
            results.append(entry)

        log.info("Batch analysis: %d/%d items relevant", len(results), len(items))
        return results

    except Exception as exc:
        log.error("Batch analysis failed: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Email formatting
# ---------------------------------------------------------------------------

PILLAR_ORDER = ["ADOPTION FAILURE", "WORKFORCE ANXIETY", "GOVERNANCE"]


def format_email(analyzed: list[dict], run_date: str) -> str:
    count = len(analyzed)
    lines = [
        "GOOD MORNING, DENISE.",
        "",
        f"Here's your daily AI briefing. {count} item{'s' if count != 1 else ''} flagged across your three content pillars.",
        "",
    ]

    if count == 0:
        lines += [
            "Nothing relevant flagged today.",
            "",
            "The system ran successfully. No items passed the three-pillar relevance filter.",
            "",
        ]
        lines.append(_footer())
        return "\n".join(lines)

    grouped: dict[str, list[dict]] = {p: [] for p in PILLAR_ORDER}
    secondary: list[dict] = []

    for item in analyzed:
        group = item.get("pillar_group", "OTHER")
        is_primary = item.get("is_primary", True)
        if not is_primary:
            secondary.append(item)
        elif group in grouped:
            grouped[group].append(item)
        else:
            secondary.append(item)

    empty_pillars = []
    for pillar in PILLAR_ORDER:
        items_in_pillar = grouped[pillar]
        if not items_in_pillar:
            empty_pillars.append(pillar)
            continue
        lines.append(pillar)
        lines.append("-" * len(pillar))
        for entry in items_in_pillar:
            lines.append(_format_entry(entry))
        lines.append("")

    if secondary:
        lines.append("SECONDARY SOURCE FLAGS")
        lines.append("----------------------")
        lines.append("Items from Meta, Apple, or xAI. Same format; lower authority weighting.")
        lines.append("")
        for entry in secondary:
            lines.append(_format_entry(entry))
        lines.append("")

    if empty_pillars:
        lines.append("Nothing relevant today in: " + ", ".join(empty_pillars))
        lines.append("")

    lines.append(_footer())
    return "\n".join(lines)


def _format_entry(entry: dict) -> str:
    def field(label: str) -> str:
        val = entry.get(label, "").strip()
        return f"{label}: {val}" if val else ""

    parts = [
        field("SOURCE"),
        field("HEADLINE"),
        field("PILLAR"),
        field("WHAT IT SAYS"),
        field("WHY IT MATTERS"),
        field("DT'S TAKE"),
        "",
    ]
    return "\n".join(p for p in parts if p is not None)


def _footer() -> str:
    return "Built by DT Daily Briefing System. Edit sources and pillars in config.py."


# ---------------------------------------------------------------------------
# Gmail delivery
# ---------------------------------------------------------------------------

def get_gmail_service():
    if not CREDENTIALS_FILE.exists():
        raise FileNotFoundError(
            "credentials.json not found. Run auth.py to set up Gmail credentials."
        )
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), GMAIL_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            TOKEN_FILE.write_text(creds.to_json())
            TOKEN_FILE.chmod(0o600)
        else:
            raise RuntimeError(
                "Gmail token missing or invalid. Run auth.py to authorize."
            )
    return build("gmail", "v1", credentials=creds)


def _build_message(subject: str, body: str, recipient: str) -> dict:
    msg = MIMEText(body, "plain", "utf-8")
    msg["To"] = recipient
    msg["Subject"] = subject
    return {"raw": base64.urlsafe_b64encode(msg.as_bytes()).decode()}


def send_email(service, subject: str, body: str, recipient: str) -> bool:
    for attempt in range(1, 3):
        try:
            service.users().messages().send(
                userId="me", body=_build_message(subject, body, recipient)
            ).execute()
            log.info("Email sent to %s (attempt %d)", recipient, attempt)
            return True
        except HttpError as exc:
            log.error("Gmail send failed (attempt %d): %s", attempt, exc)
            if attempt == 1:
                log.info("Retrying in 60 seconds...")
                time.sleep(60)
    return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        log.error("ANTHROPIC_API_KEY not set. Add it to .env")
        sys.exit(1)

    recipient = config.RECIPIENT_EMAIL
    if not recipient:
        log.error("RECIPIENT_EMAIL is empty in config.py. Add your Gmail address.")
        sys.exit(1)

    log.info("=== DT Daily AI Briefing starting ===")
    client = Anthropic(api_key=api_key)
    run_date = datetime.now().strftime("%A, %B ") + str(datetime.now().day)

    # 1. Collect
    rss_primary = fetch_rss_feeds(config.RSS_FEEDS_PRIMARY, is_primary=True)
    rss_secondary = fetch_rss_feeds(config.RSS_FEEDS_SECONDARY, is_primary=False)
    search_items = run_web_searches(config.SEARCH_QUERIES, client)

    all_items = deduplicate(rss_primary + rss_secondary + search_items)
    log.info("Total items after dedup: %d", len(all_items))

    # 2. Analyze — single batched API call
    analyzed = analyze_all_items(all_items, client)
    log.info("Items passing relevance filter: %d", len(analyzed))

    # 3. Format & send
    count = len(analyzed)
    subject = f"AI Briefing: {run_date} -- {count} item{'s' if count != 1 else ''} flagged"
    body = format_email(analyzed, run_date)

    try:
        gmail = get_gmail_service()
        success = send_email(gmail, subject, body, recipient)
        if not success:
            log.error("Email delivery failed after retry. Check briefing.log.")
    except Exception as exc:
        log.error("Gmail service error: %s", exc)

    log.info("=== DT Daily AI Briefing complete ===")


if __name__ == "__main__":
    main()
