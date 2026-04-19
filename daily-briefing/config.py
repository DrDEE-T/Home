# config.py — Edit this file to customize your daily briefing.
# Do NOT put secrets here. Secrets go in .env

RECIPIENT_EMAIL = "drdee20200@gmail.com"

SEND_HOUR = 7  # 24-hour format; used only if running as daemon, not via cron

RSS_FEEDS_PRIMARY = [
    "https://venturebeat.com/category/ai/feed/",
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
    "https://feeds.arstechnica.com/arstechnica/technology-lab",
    "https://www.technologyreview.com/feed/",
    "https://hbr.org/topic/technology/rss",
    "https://blog.google/technology/ai/rss/",
    "https://blogs.microsoft.com/ai/feed/",
    "https://blogs.nvidia.com/feed/",
]

RSS_FEEDS_SECONDARY = [
    "https://openai.com/blog/rss.xml",
    "https://www.anthropic.com/rss.xml",
    "https://ai.meta.com/blog/rss.xml",
    "https://machinelearning.apple.com/rss.xml",
]

SEARCH_QUERIES = [
    "AI workforce impact job displacement news today",
    "enterprise AI adoption failure governance news this week",
    "OpenAI OR Anthropic OR Google OR Microsoft AI announcement today",
]

ANTHROPIC_MODEL = "claude-sonnet-4-6"   # used for web search
ANALYSIS_MODEL = "claude-haiku-4-5-20251001"  # used for article analysis (cheaper)
MAX_TOKENS = 4000  # shared budget for the single batch analysis call
LOOKBACK_HOURS = 24
