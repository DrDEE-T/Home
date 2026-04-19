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

FILTER_PROMPT = """You are screening news items for relevance to Dr. Denise Turley, an AI implementation practitioner. Screen each item against her three content pillars. Drop anything that does not clearly connect to at least one.

Pillar 1. Adoption failure: why AI implementations stall, the role of mindset, culture, and organizational commitment.
Pillar 2. Workforce anxiety: how AI affects jobs, skills, workplace behavior, and professional fears.
Pillar 3. Governance: practical governance, responsible AI, compliance, and risk management inside real organizations.

Return ONLY a valid JSON array. One object per item in order:
[
  {
    "item": 1,
    "relevant": true,
    "pillar": "Adoption failure",
    "source": "publication name",
    "headline": "article headline",
    "summary": "one sentence: only what the source explicitly states"
  },
  {
    "item": 2,
    "relevant": false
  }
]

Use exactly one of these pillar values: Adoption failure, Workforce anxiety, Governance.
Do not force relevance. If it does not clearly fit, mark relevant: false."""

SYNTHESIS_PROMPT = """You are the strategic content advisor for Dr. Denise Turley. She is an AI implementation practitioner and SVP of Technology, Data and AI at a national business association. She teaches AI to professionals in healthcare, finance, legal, and nonprofit sectors. Her LinkedIn audience expects practitioner insight, not commentary. They have already read the headlines.

You have just reviewed today's relevant AI news items. Your job is to think across them — not summarize them — and make one decision: is there something worth DT's voice today?

DT does not post every day. She posts when she has something to say that her audience cannot get from a generic AI newsletter. That means:
- A pattern the sources collectively reveal that practitioners are not naming yet
- A specific failure mode she has seen in the room that today's data confirms
- A governance or workforce insight with direct relevance to healthcare, finance, legal, or nonprofit professionals

If today's news is thin, repetitive, or covered adequately elsewhere, the recommendation is NO. That is a legitimate and valuable output.

Return your response in exactly this structure:

TODAY'S THEME
[2 to 3 sentences. What is the dominant pattern across today's items? What are the sources collectively pointing at, taken together? Do not list the sources. Synthesize them.]

POST RECOMMENDATION: [YES / NO / HOLD]

REASONING
[2 to 3 sentences. Why post or why not. Be specific. If NO, state what would need to be true for this to be worth posting. If HOLD, state what you are waiting for.]

DRAFT POST
[Only include if recommendation is YES. Write a 150 to 200 word LinkedIn post in DT's voice. First person. Practitioner perspective. Open with a specific observation, not a question. Cite the specific data points from today's sources. Connect to what this means for professionals in at least one of her sectors: healthcare, finance, legal, or nonprofit. Close with one sentence that only someone with implementation experience would write. No hype. No em dashes. No generic AI cheerleading.]

REFERENCE ITEMS
[Only include if recommendation is YES or HOLD. Bullet list of the 2 to 3 strongest source and headline combinations that back the theme. Format: Source: Headline]"""

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
# Stage 1: Filter items for pillar relevance (Haiku — cheap)
# ---------------------------------------------------------------------------

def filter_items(items: list[dict], client: Anthropic) -> list[dict]:
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
            max_tokens=3000,
            system=FILTER_PROMPT,
            messages=[{"role": "user", "content": f"Screen these {len(items)} items:\n\n{numbered}"}],
        )
        raw = response.content[0].text.strip()
        parsed = _extract_json_array(raw)
        if not parsed:
            log.error("Could not parse filter JSON")
            return []

        results = []
        for entry in parsed:
            if not entry.get("relevant"):
                continue
            idx = entry.get("item", 1) - 1
            source_item = items[idx] if 0 <= idx < len(items) else {}
            entry["is_primary"] = source_item.get("is_primary", True)
            entry["url"] = source_item.get("url", "")
            results.append(entry)

        log.info("Filter: %d/%d items relevant", len(results), len(items))
        return results

    except Exception as exc:
        log.error("Filter stage failed: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Stage 2: Synthesize across relevant items (Sonnet — quality)
# ---------------------------------------------------------------------------

def synthesize(relevant: list[dict], client: Anthropic) -> str:
    if not relevant:
        return ""

    items_text = ""
    for item in relevant:
        items_text += (
            f"Source: {item.get('source', '')}\n"
            f"Headline: {item.get('headline', '')}\n"
            f"Pillar: {item.get('pillar', '')}\n"
            f"Summary: {item.get('summary', '')}\n\n"
        )

    try:
        response = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=config.MAX_TOKENS,
            system=SYNTHESIS_PROMPT,
            messages=[{"role": "user", "content": f"Today's relevant items:\n\n{items_text}"}],
        )
        return response.content[0].text.strip()
    except Exception as exc:
        log.error("Synthesis failed: %s", exc)
        return ""


# ---------------------------------------------------------------------------
# Email formatting — HTML
# ---------------------------------------------------------------------------

PILLAR_COLORS = {
    "Adoption failure":  "#7c3aed",
    "Workforce anxiety": "#2563eb",
    "Governance":        "#0e7490",
}

def format_email(relevant: list[dict], synthesis: str, run_date: str) -> str:
    count = len(relevant)

    def section(title: str, content: str, color: str = "#7b6fa0") -> str:
        return f"""
        <tr><td style="padding:24px 32px 0;">
          <p style="margin:0 0 8px;font-size:11px;font-weight:700;letter-spacing:2px;
                    text-transform:uppercase;color:{color};">{title}</p>
          <div style="border-left:3px solid {color};padding-left:16px;
                      color:#d4c8f0;font-size:15px;line-height:1.7;">{content}</div>
        </td></tr>"""

    def ref_item(item: dict) -> str:
        pillar = item.get("pillar", "")
        color = PILLAR_COLORS.get(pillar, "#7b6fa0")
        src = item.get("source", "")
        hl = item.get("headline", "")
        sm = item.get("summary", "")
        url = item.get("url", "")
        hl_html = f'<a href="{url}" style="color:#c4b5fd;text-decoration:none;">{hl}</a>' if url else hl
        return f"""
        <tr><td style="padding:16px 32px 0;">
          <div style="background:#1e1535;border-radius:8px;padding:16px 20px;
                      border-left:3px solid {color};">
            <p style="margin:0 0 4px;font-size:11px;font-weight:700;letter-spacing:1px;
                      text-transform:uppercase;color:{color};">{pillar} &nbsp;|&nbsp;
                      <span style="color:#8b7db5;">{src}</span></p>
            <p style="margin:0 0 8px;font-size:15px;font-weight:600;color:#f0ebff;">{hl_html}</p>
            <p style="margin:0;font-size:14px;color:#a89ec8;line-height:1.6;">{sm}</p>
          </div>
        </td></tr>"""

    # Parse synthesis into sections
    def extract(text: str, label: str, next_labels: list[str]) -> str:
        pattern = rf"{re.escape(label)}\s*(.*?)(?={'|'.join(re.escape(l) for l in next_labels)}|$)"
        m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return m.group(1).strip() if m else ""

    syn_labels = ["TODAY'S THEME", "POST RECOMMENDATION", "REASONING", "DRAFT POST", "REFERENCE ITEMS"]
    theme     = extract(synthesis, "TODAY'S THEME",       syn_labels[1:])
    rec_line  = extract(synthesis, "POST RECOMMENDATION:", syn_labels[2:]).strip().upper()
    if not rec_line:
        rec_line = extract(synthesis, "POST RECOMMENDATION", syn_labels[2:]).strip().upper()
    reasoning = extract(synthesis, "REASONING",           syn_labels[3:])
    draft     = extract(synthesis, "DRAFT POST",          syn_labels[4:])
    refs      = extract(synthesis, "REFERENCE ITEMS",     [])

    rec_color = {"YES": "#22c55e", "NO": "#ef4444", "HOLD": "#f59e0b"}.get(rec_line[:4].strip(), "#7b6fa0")

    # Build HTML
    rows = []

    if not synthesis:
        rows.append(section("No Analysis Available",
            "The synthesis step did not return output. Check briefing.log.", "#ef4444"))
    else:
        if theme:
            rows.append(section("TODAY'S THEME", theme.replace("\n", "<br>"), "#7b6fa0"))

        rec_display = rec_line if rec_line else "UNKNOWN"
        rows.append(f"""
        <tr><td style="padding:24px 32px 0;">
          <p style="margin:0 0 8px;font-size:11px;font-weight:700;letter-spacing:2px;
                    text-transform:uppercase;color:#7b6fa0;">POST RECOMMENDATION</p>
          <div style="display:inline-block;background:{rec_color}22;border:1px solid {rec_color};
                      border-radius:6px;padding:6px 18px;">
            <span style="font-size:18px;font-weight:800;color:{rec_color};">{rec_display}</span>
          </div>
        </td></tr>""")

        if reasoning:
            rows.append(section("REASONING", reasoning.replace("\n", "<br>"), "#7b6fa0"))

        if draft:
            draft_html = draft.replace("\n", "<br>")
            rows.append(f"""
            <tr><td style="padding:24px 32px 0;">
              <p style="margin:0 0 8px;font-size:11px;font-weight:700;letter-spacing:2px;
                        text-transform:uppercase;color:#22c55e;">DRAFT POST</p>
              <div style="background:#0d2818;border:1px solid #22c55e44;border-radius:8px;
                          padding:20px 24px;color:#d4f0dc;font-size:15px;line-height:1.8;
                          font-style:italic;">{draft_html}</div>
            </td></tr>""")

        if refs:
            refs_html = "<br>".join(
                f'<span style="color:#7b6fa0;">&#8250;</span> {line.strip().lstrip("-").strip()}'
                for line in refs.strip().splitlines() if line.strip()
            )
            rows.append(section("REFERENCE ITEMS", refs_html, "#7b6fa0"))

    if count == 0:
        rows.append(section("NO ITEMS FLAGGED",
            "The system ran successfully. No articles passed the three-pillar relevance filter today.",
            "#ef4444"))
    else:
        rows.append(f"""
        <tr><td style="padding:24px 32px 0;">
          <p style="margin:0 0 12px;font-size:11px;font-weight:700;letter-spacing:2px;
                    text-transform:uppercase;color:#7b6fa0;">SOURCE ITEMS ({count})</p>
        </td></tr>""")
        for item in relevant:
            rows.append(ref_item(item))

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#0a0812;font-family:'Segoe UI',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0812;">
<tr><td align="center" style="padding:32px 16px;">
<table width="640" cellpadding="0" cellspacing="0"
       style="background:#120f1e;border-radius:12px;border:1px solid #2d2548;max-width:640px;">

  <tr><td style="padding:32px 32px 24px;border-bottom:1px solid #2d2548;">
    <p style="margin:0 0 4px;font-size:12px;letter-spacing:3px;text-transform:uppercase;
              color:#7b6fa0;">DT DAILY BRIEFING</p>
    <h1 style="margin:0;font-size:22px;font-weight:700;color:#f0ebff;">{run_date}</h1>
    <p style="margin:6px 0 0;font-size:13px;color:#6b5f8a;">
      {count} item{'s' if count != 1 else ''} flagged across three content pillars</p>
  </td></tr>

  {"".join(rows)}

  <tr><td style="padding:24px 32px 32px;border-top:1px solid #2d2548;margin-top:24px;">
    <p style="margin:0;font-size:11px;color:#4a4060;">
      DT Daily Briefing System. Edit sources and pillars in config.py.</p>
  </td></tr>

</table>
</td></tr>
</table>
</body></html>"""
    return html


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
    msg = MIMEText(body, "html", "utf-8")
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

    # 2a. Filter for pillar relevance (Haiku)
    relevant = filter_items(all_items, client)

    # 2b. Synthesize across relevant items (Sonnet)
    synthesis = synthesize(relevant, client) if relevant else ""
    if not synthesis and relevant:
        log.warning("Synthesis returned empty — sending items without strategic analysis")

    # 3. Format & send
    count = len(relevant)
    rec_match = re.search(r"POST RECOMMENDATION[:\s]+(\w+)", synthesis, re.IGNORECASE)
    rec = rec_match.group(1).upper() if rec_match else "N/A"
    subject = f"AI Briefing {run_date} | {count} items | Post: {rec}"
    body = format_email(relevant, synthesis, run_date)

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
