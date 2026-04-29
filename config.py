import os

# ベトナム現地メディアのRSS。経営判断に資する記事が拾える主要紙を選定。
RSS_FEEDS = [
    ("vnexpress", "https://vnexpress.net/rss/kinh-doanh.rss"),         # ビジネス
    ("vnexpress_realestate", "https://vnexpress.net/rss/bat-dong-san.rss"),  # 不動産
    ("vnexpress_travel", "https://vnexpress.net/rss/du-lich.rss"),     # 旅行・観光
    ("vnexpress_law", "https://vnexpress.net/rss/phap-luat.rss"),      # 法律
    ("vnexpress_intl", "https://e.vnexpress.net/rss/news.rss"),        # 英語版・主要ニュース
    ("tuoitre", "https://tuoitre.vn/rss/kinh-doanh.rss"),
    ("thanhnien", "https://thanhnien.vn/rss/home.rss"),
]

FETCH_INTERVAL_MINUTES = int(os.environ.get("FETCH_INTERVAL_MINUTES", "30"))
MAX_ARTICLES_PER_FEED = int(os.environ.get("MAX_ARTICLES_PER_FEED", "10"))

CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5-20251001")
MAX_BODY_CHARS = 4000

DB_PATH = os.environ.get("DB_PATH", "vn_news.db")

# 経営者向けに調整した8カテゴリ
VALID_CATEGORIES = [
    "不動産",
    "観光",
    "経済",
    "規制・法律",
    "為替・金融",
    "サウナ・ウェルネス",
    "リスク情報",
    "その他",
]

# 重要度: 3=高(要確認) / 2=中(参考) / 1=低(雑報)
VALID_IMPORTANCE = (1, 2, 3)
