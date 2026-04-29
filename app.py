import logging
import os
import threading

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from flask import Flask, abort, jsonify, render_template
from sqlalchemy.pool import NullPool

load_dotenv()

from config import DB_PATH, FETCH_INTERVAL_MINUTES
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
        # Render exposes "postgres://", SQLAlchemy 2.x requires "postgresql://"
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        if url.startswith("postgresql://") and "+psycopg2" not in url:
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return url
    return f"sqlite:///{os.path.abspath(DB_PATH)}"


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = _build_db_uri()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # Avoid sharing psycopg2 connections across threads (scheduler + gunicorn workers).
    # Sharing a single SSL connection across threads causes "decryption failed or bad record mac".
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "poolclass": NullPool,
        "pool_pre_ping": True,
    }

    db.init_app(app)
    with app.app_context():
        db.create_all()

    @app.route("/")
    def index():
        articles = (
            Article.query.order_by(
                Article.published_at.desc().nullslast(),
                Article.created_at.desc(),
            )
            .limit(50)
            .all()
        )
        return render_template("index.html", articles=articles)

    @app.route("/article/<int:article_id>")
    def detail(article_id: int):
        article = Article.query.get(article_id)
        if article is None:
            abort(404)
        return render_template("detail.html", article=article)

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

    # initial run on startup so the DB is not empty
    threading.Thread(target=fetch_all, args=(app,), daemon=True).start()
    return scheduler


app = create_app()


def _scheduler_should_run() -> bool:
    if os.environ.get("DISABLE_SCHEDULER") == "1":
        return False
    if app.debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        return False
    return True


# Start scheduler at import time (so it works under gunicorn too).
if _scheduler_should_run():
    _start_scheduler(app)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=False)
