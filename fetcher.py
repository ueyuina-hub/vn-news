import logging
import re
from datetime import datetime
from time import mktime
from typing import Optional

import feedparser
import trafilatura

from config import MAX_ARTICLES_PER_FEED, RSS_FEEDS
from db import db
from models import Article
from translator import translate_article

logger = logging.getLogger(__name__)


def _strip_html(html: str) -> str:
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _parse_published(entry) -> Optional[datetime]:
    for key in ("published_parsed", "updated_parsed"):
        t = getattr(entry, key, None) or entry.get(key) if hasattr(entry, "get") else None
        if t:
            try:
                return datetime.fromtimestamp(mktime(t))
            except Exception:
                pass
    return None


def _extract_full_body(url: str, fallback: str) -> str:
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            extracted = trafilatura.extract(
                downloaded, include_comments=False, include_tables=False, favor_recall=True
            )
            if extracted and len(extracted.strip()) >= 80:
                return extracted.strip()
    except Exception as e:
        logger.warning("trafilatura failed for %s: %s", url, e)
    return fallback


def _process_feed(source: str, url: str) -> int:
    parsed = feedparser.parse(url)
    if parsed.bozo:
        logger.warning("RSS parse warning for %s: %s", url, parsed.bozo_exception)

    saved = 0
    for entry in parsed.entries[:MAX_ARTICLES_PER_FEED]:
        link = (entry.get("link") or "").strip()
        if not link:
            continue

        if db.session.query(Article.id).filter_by(url=link).first():
            continue

        title_vi = (entry.get("title") or "").strip()
        rss_body = _strip_html(entry.get("summary") or entry.get("description") or "")
        body_vi = _extract_full_body(link, rss_body)

        if not title_vi or not body_vi:
            logger.info("Skipping (empty title/body): %s", link)
            continue

        try:
            translated = translate_article(title_vi, body_vi)
        except Exception as e:
            logger.error("Translation failed for %s: %s", link, e)
            db.session.rollback()
            continue

        article = Article(
            source=source,
            url=link,
            title_vi=title_vi,
            title_ja=translated["title_ja"],
            body_vi=body_vi,
            body_ja=translated["body_ja"],
            summary_ja=translated["summary_ja"],
            category=translated["category"],
            importance=translated.get("importance", 1),
            exec_comment=translated.get("exec_comment", ""),
            easy_summary=translated.get("easy_summary", ""),
            published_at=_parse_published(entry),
        )
        db.session.add(article)
        try:
            db.session.commit()
            saved += 1
            logger.info("[%s] saved: %s", source, translated["title_ja"][:60])
        except Exception as e:
            db.session.rollback()
            logger.error("DB commit failed for %s: %s", link, e)

    return saved


def fetch_all(app=None):
    """Fetch all configured RSS feeds, translate new entries, persist to DB."""
    ctx = app.app_context() if app is not None else None
    if ctx:
        ctx.push()
    try:
        total = 0
        for source, url in RSS_FEEDS:
            try:
                n = _process_feed(source, url)
                logger.info("Fetched %d new articles from %s", n, source)
                total += n
            except Exception as e:
                logger.exception("Feed processing failed for %s: %s", source, e)
                # Reset the session so the next feed can run independently.
                try:
                    db.session.rollback()
                except Exception:
                    pass
        logger.info("fetch_all done: %d new articles", total)
        return total
    finally:
        if ctx:
            ctx.pop()
