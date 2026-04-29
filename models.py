from datetime import datetime

from db import db


class Article(db.Model):
    __tablename__ = "article"

    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(64), nullable=False, index=True)
    url = db.Column(db.String(1024), nullable=False, unique=True, index=True)

    title_vi = db.Column(db.String(1024), nullable=False)
    title_ja = db.Column(db.String(1024), nullable=False)
    body_vi = db.Column(db.Text, nullable=False)
    body_ja = db.Column(db.Text, nullable=False)
    summary_ja = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(32), nullable=False, index=True)

    # 経営者向け追加項目
    importance = db.Column(db.Integer, nullable=False, default=1, index=True)  # 1..3
    exec_comment = db.Column(db.Text, nullable=False, default="")               # なぜ重要か(一言)

    # ブックマーク・既読管理
    is_bookmarked = db.Column(db.Boolean, nullable=False, default=False, index=True)
    is_read = db.Column(db.Boolean, nullable=False, default=False, index=True)
    read_at = db.Column(db.DateTime, nullable=True)

    published_at = db.Column(db.DateTime, nullable=True, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @property
    def summary_lines(self):
        return [line for line in (self.summary_ja or "").split("\n") if line.strip()]

    @property
    def importance_label(self):
        return {3: "高", 2: "中", 1: "低"}.get(self.importance, "低")
