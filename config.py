import os

RSS_FEEDS = [
    ("vnexpress", "https://vnexpress.net/rss/tin-moi-nhat.rss"),
    ("tuoitre", "https://tuoitre.vn/rss/tin-moi-nhat.rss"),
    ("thanhnien", "https://thanhnien.vn/rss/home.rss"),
    ("vnexpress_intl", "https://e.vnexpress.net/rss/news.rss"),
]

FETCH_INTERVAL_MINUTES = int(os.environ.get("FETCH_INTERVAL_MINUTES", "30"))
MAX_ARTICLES_PER_FEED = int(os.environ.get("MAX_ARTICLES_PER_FEED", "10"))

CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5-20251001")
MAX_BODY_CHARS = 4000

DB_PATH = os.environ.get("DB_PATH", "vn_news.db")

VALID_CATEGORIES = ["政治", "経済", "社会", "観光", "国際"]
