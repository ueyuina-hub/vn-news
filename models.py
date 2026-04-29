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
    category = db.Column(db.String(16), nullable=False, index=True)

    published_at = db.Column(db.DateTime, nullable=True, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @property
    def summary_lines(self):
        return [line for line in (self.summary_ja or "").split("\n") if line.strip()]
