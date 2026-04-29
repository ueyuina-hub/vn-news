"""APIキー無しでも画面確認できるよう、サンプル記事をDBに投入するスクリプト。

使い方:
    python seed_sample.py             # サンプル6件を追加(URL重複はスキップ)
    python seed_sample.py --reset     # 既存DBをクリアしてからサンプル投入
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta

# .env を読まなくても動作するようにする(APIキー不要)
os.environ.setdefault("ANTHROPIC_API_KEY", "dummy-not-used-by-seed")
# seed実行時はスケジューラを起動させない
os.environ["DISABLE_SCHEDULER"] = "1"

from app import app  # noqa: E402  Flaskアプリ + db初期化を流用
from db import db  # noqa: E402
from models import Article  # noqa: E402


SAMPLES = [
    {
        "source": "vnexpress",
        "url": "https://example.com/sample/vn-realestate-2026-04",
        "title_vi": "Giá căn hộ TP HCM tăng 12% trong quý I",
        "title_ja": "ホーチミン市のマンション価格、第1四半期に12%上昇",
        "body_vi": "Giá căn hộ trung và cao cấp tại TP HCM tăng mạnh do nguồn cung hạn chế và nhu cầu của nhà đầu tư nước ngoài. ...",
        "body_ja": (
            "ホーチミン市のマンション価格が2026年第1四半期に前年同期比で12%上昇したと地元紙が報じた。"
            "中〜高価格帯の上昇が顕著で、外資系投資家の需要と供給制限が背景にある。\n\n"
            "市場関係者は、年後半にかけてさらに5〜8%上昇する可能性があると見ている。"
            "ただし、政府の不動産融資規制や外資保有比率の議論次第で減速する可能性もある。"
        ),
        "summary_ja": (
            "ホーチミン市の中高価格帯マンションが前年比12%上昇\n"
            "外資の買い需要と供給不足が押し上げ要因\n"
            "規制議論次第で年後半は減速の可能性も"
        ),
        "category": "不動産",
        "importance": 3,
        "exec_comment": "ホテル・サウナ施設の用地取得コストに直結。賃料相場も上昇基調のため、新規物件のリース判断は早めに。",
        "published_at": datetime.utcnow() - timedelta(hours=4),
    },
    {
        "source": "vnexpress_intl",
        "url": "https://example.com/sample/vn-tourism-2026-04",
        "title_vi": "Khách quốc tế đến Việt Nam vượt 5 triệu lượt trong 4 tháng",
        "title_ja": "ベトナム訪問外国人客、1〜4月で500万人超え",
        "body_vi": "Việt Nam đón hơn 5 triệu lượt khách quốc tế trong 4 tháng đầu năm, tăng 23% so với cùng kỳ. ...",
        "body_ja": (
            "ベトナム観光総局によると、2026年1〜4月の訪越外国人客数は500万人を超え、前年同期比で23%増加した。"
            "韓国・中国・米国・日本からの旅行者が伸びており、ハノイとダナンが特に人気。\n\n"
            "政府は年間の訪問者目標を1,800万人に上方修正。ビザ免除対象国の拡大も検討中とされる。"
        ),
        "summary_ja": (
            "1〜4月の訪越外国人客が500万人超、前年比23%増\n"
            "韓中米日が主要市場、ハノイ・ダナンに集中\n"
            "政府は年間目標を1,800万人に上方修正"
        ),
        "category": "観光",
        "importance": 3,
        "exec_comment": "観光客回復はホテル併設サウナの稼働率に直結。富裕層客の割合が高い韓国・日本市場の伸びは追い風。",
        "published_at": datetime.utcnow() - timedelta(hours=10),
    },
    {
        "source": "tuoitre",
        "url": "https://example.com/sample/vn-fx-2026-04",
        "title_vi": "Tỷ giá USD/VND chạm mức cao kỷ lục",
        "title_ja": "USD/VND為替、過去最高水準に到達",
        "body_vi": "Tỷ giá USD/VND tiếp tục tăng, đạt mức kỷ lục mới do áp lực từ thị trường quốc tế. ...",
        "body_ja": (
            "USD/VND相場が連日上昇し、過去最高水準を更新した。米金利の高止まりとドル高圧力が背景。"
            "ベトナム国家銀行は介入の準備を示唆しているが、過度な防衛は外貨準備を消耗させる懸念もある。\n\n"
            "輸入企業はコスト増、外貨建て負債を抱える企業は返済負担の増加に直面している。"
        ),
        "summary_ja": (
            "USD/VND為替が過去最高水準を更新\n"
            "米金利高止まりとドル高が主因\n"
            "輸入コストと外貨建て債務の負担増に注意"
        ),
        "category": "為替・金融",
        "importance": 3,
        "exec_comment": "資材・什器の輸入コストが上昇。日本円ベースの送金タイミング次第で利益率に影響するため、為替予約の検討余地あり。",
        "published_at": datetime.utcnow() - timedelta(hours=20),
    },
    {
        "source": "thanhnien",
        "url": "https://example.com/sample/vn-foreign-investment-law-2026-04",
        "title_vi": "Sửa đổi Luật Đầu tư: nới lỏng tỷ lệ sở hữu nước ngoài",
        "title_ja": "投資法改正案、外資保有比率を緩和へ",
        "body_vi": "Quốc hội đang xem xét sửa đổi Luật Đầu tư cho phép nâng tỷ lệ sở hữu nước ngoài trong một số ngành dịch vụ. ...",
        "body_ja": (
            "ベトナム国会で投資法の改正案が審議されている。サービス業の一部について、外資の保有比率上限の引き上げが含まれる。"
            "対象には小売、ヘルスケア、フィットネス・ウェルネス施設が含まれる見込み。\n\n"
            "成立すれば早ければ2026年下期に施行される見通しで、日系企業の単独進出も現実味を帯びる。"
        ),
        "summary_ja": (
            "投資法改正案で外資保有比率の緩和が検討中\n"
            "小売・ヘルスケア・ウェルネスが対象に\n"
            "成立すれば2026年下期施行の見込み"
        ),
        "category": "規制・法律",
        "importance": 3,
        "exec_comment": "サウナ・ウェルネスの単独出資進出が可能になり得る重要法案。合弁解消や追加出資の戦略を再検討するタイミング。",
        "published_at": datetime.utcnow() - timedelta(hours=28),
    },
    {
        "source": "vnexpress",
        "url": "https://example.com/sample/vn-wellness-trend-2026-04",
        "title_vi": "Xu hướng spa và sauna cao cấp bùng nổ tại Hà Nội",
        "title_ja": "ハノイで高級スパ・サウナ需要が急拡大",
        "body_vi": "Các cơ sở spa, sauna phong cách Bắc Âu và Nhật Bản đang thu hút khách hàng có thu nhập cao. ...",
        "body_ja": (
            "ハノイ市内で、北欧スタイルや日本式の高級スパ・サウナ施設が高所得層を中心に人気を集めている。"
            "新規開業ペースは前年の1.7倍で、平均客単価は80万VND前後。\n\n"
            "ホテル併設型と単独店型の両方が伸びており、リピーター比率も改善している。"
        ),
        "summary_ja": (
            "ハノイで北欧式・日本式の高級サウナが急成長\n"
            "新規開業は前年の1.7倍、客単価は約80万VND\n"
            "ホテル併設・単独店ともリピート率が上昇"
        ),
        "category": "サウナ・ウェルネス",
        "importance": 3,
        "exec_comment": "本業ど真ん中の追い風トレンド。客単価データは価格戦略の参考に、開業ペースは競合参入の指標として要モニタ。",
        "published_at": datetime.utcnow() - timedelta(hours=36),
    },
    {
        "source": "tuoitre",
        "url": "https://example.com/sample/vn-incident-2026-04",
        "title_vi": "Cảnh báo trộm cắp gia tăng tại khu du lịch Đà Nẵng",
        "title_ja": "ダナン観光エリアで窃盗被害が増加、警察が注意喚起",
        "body_vi": "Cảnh sát Đà Nẵng cảnh báo du khách về tình trạng móc túi và trộm cắp gia tăng. ...",
        "body_ja": (
            "ダナン市警察は、観光エリアでスリ・置き引きの被害が増加しているとして注意喚起した。"
            "特にビーチ周辺と夜間市場で被害報告が多く、外国人観光客が標的になりやすい。\n\n"
            "警察はパトロール強化と、観光事業者への防犯協力を呼びかけている。"
        ),
        "summary_ja": (
            "ダナンの観光地で窃盗被害が増加傾向\n"
            "ビーチ周辺と夜間市場で被害集中\n"
            "警察がパトロールと事業者協力を強化"
        ),
        "category": "リスク情報",
        "importance": 2,
        "exec_comment": "ダナンに出張・視察予定があれば貴重品管理に注意。施設運営でも顧客への注意喚起や荷物管理サービスの強化を検討。",
        "published_at": datetime.utcnow() - timedelta(days=2),
    },
]


def seed(reset: bool) -> None:
    with app.app_context():
        if reset:
            print("[seed] resetting article table...")
            Article.query.delete()
            db.session.commit()

        added = 0
        for s in SAMPLES:
            exists = Article.query.filter_by(url=s["url"]).first()
            if exists:
                continue
            db.session.add(Article(**s))
            added += 1
        db.session.commit()
        total = Article.query.count()
        print(f"[seed] added {added} sample articles (total in DB: {total})")


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed sample articles for vn-news")
    parser.add_argument("--reset", action="store_true", help="既存記事をすべて削除してから投入")
    args = parser.parse_args()
    seed(reset=args.reset)
    return 0


if __name__ == "__main__":
    sys.exit(main())
