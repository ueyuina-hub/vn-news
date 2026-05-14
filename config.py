import os

# 取り扱う地域(タブメニュー順)
REGIONS = [
    {"code": "vietnam", "label": "🇻🇳 ベトナム"},
    {"code": "chiangmai", "label": "🇹🇭 チェンマイ"},
]
DEFAULT_REGION = "vietnam"

# 地域別 RSS フィード
REGIONAL_FEEDS = {
    "vietnam": [
        ("vnexpress", "https://vnexpress.net/rss/kinh-doanh.rss"),
        ("vnexpress_realestate", "https://vnexpress.net/rss/bat-dong-san.rss"),
        ("vnexpress_travel", "https://vnexpress.net/rss/du-lich.rss"),
        ("vnexpress_law", "https://vnexpress.net/rss/phap-luat.rss"),
        ("vnexpress_intl", "https://e.vnexpress.net/rss/news.rss"),
        ("tuoitre", "https://tuoitre.vn/rss/kinh-doanh.rss"),
        ("thanhnien", "https://thanhnien.vn/rss/home.rss"),
    ],
    "chiangmai": [
        # タイ国内の英字主要紙(チェンマイ・タイ北部・タイ全土の不動産/観光/ホテル動向を網羅)
        ("bangkokpost_business", "https://www.bangkokpost.com/rss/data/business.xml"),
        ("bangkokpost_travel", "https://www.bangkokpost.com/rss/data/travel.xml"),
        ("bangkokpost_property", "https://www.bangkokpost.com/rss/data/property.xml"),
        ("nation_thailand", "https://www.nationthailand.com/rss-feed"),
        ("citylife_chiangmai", "https://www.chiangmaicitylife.com/feed/"),
    ],
}

# 後方互換用 (region情報なし)
RSS_FEEDS = [(s, u) for feeds in REGIONAL_FEEDS.values() for s, u in feeds]

FETCH_INTERVAL_MINUTES = int(os.environ.get("FETCH_INTERVAL_MINUTES", "30"))
MAX_ARTICLES_PER_FEED = int(os.environ.get("MAX_ARTICLES_PER_FEED", "10"))

CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5-20251001")
MAX_BODY_CHARS = 4000

DB_PATH = os.environ.get("DB_PATH", "vn_news.db")

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

VALID_IMPORTANCE = (1, 2, 3)
