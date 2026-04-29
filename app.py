import logging
import os
import threading
import traceback
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from flask import Flask, Response, abort, jsonify, render_template, request
from sqlalchemy import inspect, or_, text
from sqlalchemy.pool import NullPool
from werkzeug.exceptions import HTTPException

load_dotenv()

from config import DB_PATH, FETCH_INTERVAL_MINUTES, VALID_CATEGORIES
from db import db
from fetcher import fetch_all
from models import Article

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def _build_db_uri() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        if url.startswith("postgresql://") and "+psycopg2" not in url:
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return url
    return f"sqlite:///{os.path.abspath(DB_PATH)}"


def _light_migrate():
    """既存テーブルに新カラムが無ければ追加する軽量マイグレーション (SQLite/PG両対応)。"""
    insp = inspect(db.engine)
    if "article" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("article")}

    is_pg = db.engine.dialect.name == "postgresql"
    bool_default = "FALSE" if is_pg else "0"
    datetime_type = "TIMESTAMP" if is_pg else "DATETIME"

    statements = []
    if "importance" not in cols:
        statements.append("ALTER TABLE article ADD COLUMN importance INTEGER NOT NULL DEFAULT 1")
    if "exec_comment" not in cols:
        statements.append("ALTER TABLE article ADD COLUMN exec_comment TEXT NOT NULL DEFAULT ''")
    if "is_bookmarked" not in cols:
        statements.append(
            f"ALTER TABLE article ADD COLUMN is_bookmarked BOOLEAN NOT NULL DEFAULT {bool_default}"
        )
    if "is_read" not in cols:
        statements.append(
            f"ALTER TABLE article ADD COLUMN is_read BOOLEAN NOT NULL DEFAULT {bool_default}"
        )
    if "read_at" not in cols:
        statements.append(f"ALTER TABLE article ADD COLUMN read_at {datetime_type}")

    if not statements:
        return

    log = logging.getLogger(__name__)
    # 1ステートメントずつ独立したトランザクションで実行(1つ失敗しても他は適用)
    for stmt in statements:
        try:
            with db.engine.begin() as conn:
                conn.execute(text(stmt))
            log.info("migration applied: %s", stmt)
        except Exception as e:
            log.warning("migration step failed: %s — %s", stmt, e)


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = _build_db_uri()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "poolclass": NullPool,
        "pool_pre_ping": True,
    }

    db.init_app(app)
    with app.app_context():
        db.create_all()
        try:
            _light_migrate()
        except Exception as e:
            logging.getLogger(__name__).warning("light migration skipped: %s", e)

    # 簡易ベーシック認証(知人配布用)。BASIC_AUTH_USER と BASIC_AUTH_PASS が
    # 両方設定されている場合のみ有効化。/healthz は監視のため除外。
    @app.before_request
    def _basic_auth_guard():
        user = os.environ.get("BASIC_AUTH_USER")
        pw = os.environ.get("BASIC_AUTH_PASS")
        if not (user and pw):
            return None
        if request.path == "/healthz":
            return None
        auth = request.authorization
        if not auth or auth.username != user or auth.password != pw:
            return Response(
                "認証が必要です",
                401,
                {"WWW-Authenticate": 'Basic realm="Vietnam Briefing"'},
            )
        return None

    # 各リクエスト開始時にセッションを念のため rollback して
    # 別スレッド(fetcher)由来の PendingRollbackError を引き継がないようにする。
    @app.before_request
    def _reset_session_state():
        if request.path == "/healthz":
            return None
        try:
            db.session.rollback()
        except Exception:
            pass
        return None

    # 例外時はログにだけ詳細を残し、画面にはシンプルなメッセージを表示
    @app.errorhandler(Exception)
    def _handle_exception(e):
        if isinstance(e, HTTPException):
            return e
        logging.getLogger(__name__).exception("Unhandled exception")
        try:
            db.session.rollback()
        except Exception:
            pass
        return Response(
            "<h1>一時的にご利用いただけません</h1>"
            "<p>少し時間をおいて再度お試しください。</p>",
            500,
            {"Content-Type": "text/html; charset=utf-8"},
        )

    @app.route("/")
    def index():
        category = (request.args.get("category") or "").strip()
        q = (request.args.get("q") or "").strip()
        bookmarked = request.args.get("bookmarked") == "1"
        unread = request.args.get("unread") == "1"

        query = Article.query
        if category and category in VALID_CATEGORIES:
            query = query.filter(Article.category == category)
        if q:
            like = f"%{q}%"
            query = query.filter(
                or_(
                    Article.title_ja.like(like),
                    Article.body_ja.like(like),
                    Article.summary_ja.like(like),
                    Article.exec_comment.like(like),
                )
            )
        if bookmarked:
            query = query.filter(Article.is_bookmarked.is_(True))
        if unread:
            query = query.filter(Article.is_read.is_(False))

        articles = (
            query.order_by(
                Article.importance.desc(),
                Article.published_at.desc().nullslast(),
                Article.created_at.desc(),
            )
            .limit(80)
            .all()
        )

        # 「今日の重要ニュース3本」: 過去48hで重要度の高い順、無ければ全期間から重要度順
        cutoff = datetime.utcnow() - timedelta(hours=48)
        top3 = (
            Article.query.filter(
                or_(Article.published_at >= cutoff, Article.created_at >= cutoff)
            )
            .order_by(Article.importance.desc(), Article.published_at.desc().nullslast())
            .limit(3)
            .all()
        )
        if len(top3) < 3:
            top3 = (
                Article.query.order_by(
                    Article.importance.desc(), Article.published_at.desc().nullslast()
                )
                .limit(3)
                .all()
            )

        return render_template(
            "index.html",
            articles=articles,
            top3=top3,
            categories=VALID_CATEGORIES,
            current_category=category,
            q=q,
            bookmarked=bookmarked,
            unread=unread,
        )

    @app.route("/article/<int:article_id>")
    def detail(article_id: int):
        article = Article.query.get(article_id)
        if article is None:
            abort(404)
        # 詳細を開いた時点で自動的に既読化
        if not article.is_read:
            article.is_read = True
            article.read_at = datetime.utcnow()
            db.session.commit()
        return render_template("detail.html", article=article)

    @app.route("/article/<int:article_id>/bookmark", methods=["POST"])
    def toggle_bookmark(article_id: int):
        article = Article.query.get(article_id)
        if article is None:
            abort(404)
        article.is_bookmarked = not article.is_bookmarked
        db.session.commit()
        return jsonify({"id": article.id, "is_bookmarked": article.is_bookmarked})

    @app.route("/article/<int:article_id>/read", methods=["POST"])
    def toggle_read(article_id: int):
        article = Article.query.get(article_id)
        if article is None:
            abort(404)
        article.is_read = not article.is_read
        article.read_at = datetime.utcnow() if article.is_read else None
        db.session.commit()
        return jsonify({"id": article.id, "is_read": article.is_read})

    @app.route("/fetch", methods=["POST", "GET"])
    def manual_fetch():
        thread = threading.Thread(target=fetch_all, args=(app,), daemon=True)
        thread.start()
        return jsonify({"status": "started"}), 202

    @app.route("/healthz")
    def healthz():
        return jsonify({"status": "ok"})

    return app


def _start_scheduler(app: Flask):
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(
        func=lambda: fetch_all(app),
        trigger="interval",
        minutes=FETCH_INTERVAL_MINUTES,
        id="fetch_all",
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    threading.Thread(target=fetch_all, args=(app,), daemon=True).start()
    return scheduler


app = create_app()


def _scheduler_should_run() -> bool:
    if os.environ.get("DISABLE_SCHEDULER") == "1":
        return False
    if app.debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        return False
    return True


if _scheduler_should_run():
    _start_scheduler(app)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=False)
