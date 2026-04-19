# config.py — Edit this file to customize your daily briefing.
# Do NOT put secrets here. Secrets go in .env

RECIPIENT_EMAIL = ""  # e.g. "you@gmail.com"

SEND_HOUR = 7  # 24-hour format; used only if running as daemon, not via cron

RSS_FEEDS_PRIMARY = [
    "https://openai.com/blog/rss.xml",
    "https://www.anthropic.com/rss.xml",
    "https://blog.google/technology/ai/rss/",
    "https://blogs.microsoft.com/ai/feed/",
    "https://blogs.nvidia.com/feed/",
    "https://www.perplexity.ai/hub/blog/rss",
    "https://hbr.org/topic/technology/rss",
    "https://www.forbes.com/ai/feed/",
    "https://www.technologyreview.com/feed/",
]

RSS_FEEDS_SECONDARY = [
    "https://ai.meta.com/blog/rss.xml",
    "https://machinelearning.apple.com/rss.xml",
    "https://x.ai/blog/rss",  # skipped gracefully if unavailable
]

SEARCH_QUERIES = [
    "AI workforce impact news today",
    "enterprise AI adoption research this week",
    "AI job displacement survey latest",
    "AI governance policy news today",
    "AI implementation failure case study recent",
    "OpenAI OR Anthropic OR Google OR Microsoft AI announcement today",
]

ANTHROPIC_MODEL = "claude-sonnet-4-6"   # used for web search
ANALYSIS_MODEL = "claude-haiku-4-5-20251001"  # used for article analysis (cheaper)
MAX_TOKENS = 4000  # shared budget for the single batch analysis call
LOOKBACK_HOURS = 24
