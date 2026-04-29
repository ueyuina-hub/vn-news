# ベトナムニュース日本語版 (vn-news)

ベトナムの大手ニュースサイトのRSSを定期取得し、Claude API (Haiku 4.5) で日本語に翻訳・3行要約・カテゴリ分類して表示するFlask Webアプリ。

## 機能

- RSS定期取得 (VnExpress / Tuoi Tre / Thanh Nien / VnExpress International)
- 記事タイトル・本文・URL・公開日を SQLite に保存 (URLで重複排除)
- Claude API で本文を自然な日本語に翻訳
- 3行要約を自動生成
- 5カテゴリで自動分類 (政治 / 経済 / 社会 / 観光 / 国際)
- スマホで読みやすいレスポンシブUI (ダークモード対応)
- 一覧画面: 日本語タイトル / 3行要約 / カテゴリバッジ / 元記事リンク
- 詳細画面: 日本語訳 / 3行要約 / 原文 (折りたたみ) / 元記事リンク

## セットアップ

### 1. 仮想環境を作って依存をインストール

```bash
cd vn-news
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. `.env` を作成して APIキーを設定

```bash
cp .env.example .env
# .env を開いて ANTHROPIC_API_KEY=sk-ant-... を入れる
```

`ANTHROPIC_API_KEY` は [Anthropic Console](https://console.anthropic.com/) で発行できます。

### 3. 起動

```bash
python app.py
```

ブラウザで `http://localhost:5000` を開きます。

- 起動直後にバックグラウンドで **1回 即時 RSS 取得** が走ります
- 以降、`FETCH_INTERVAL_MINUTES` 分ごと (デフォルト 30 分) に自動取得されます
- 初回はフィード4本 × 最大10件 = 最大40記事を翻訳するため、数分かかります

### 手動取得 (任意)

```bash
curl -X POST http://localhost:5000/fetch
```

レスポンスは即座に `202` を返し、取得処理はバックグラウンドで続きます。

## ファイル構成

```
vn-news/
├── app.py            # Flask本体 + ルーティング + APScheduler
├── config.py         # RSSフィードURL、取得間隔、モデル名
├── db.py             # SQLAlchemy 初期化
├── models.py         # Article モデル
├── fetcher.py        # RSS取得 + 本文抽出 + 重複チェック + 保存
├── translator.py     # Claude API クライアント
├── templates/
│   ├── base.html
│   ├── index.html    # 一覧画面
│   └── detail.html   # 詳細画面
├── static/
│   └── style.css     # スマホ向けレスポンシブCSS
├── .env.example
├── requirements.txt
└── README.md
```

## 設定項目 (.env)

| 変数 | 既定値 | 説明 |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | (必須) | Claude API キー |
| `FETCH_INTERVAL_MINUTES` | `30` | RSS取得間隔(分) |
| `MAX_ARTICLES_PER_FEED` | `10` | 1フィード/1回あたりの処理上限 |
| `CLAUDE_MODEL` | `claude-haiku-4-5-20251001` | 使用モデル |
| `DB_PATH` | `vn_news.db` | SQLite DBファイルパス |

## 利用モデル / コストの目安

- **claude-haiku-4-5-20251001** (Haiku 4.5)
- 1記事あたり 1リクエストで「翻訳 + 3行要約 + カテゴリ分類」をまとめて処理
- システムプロンプトに prompt caching を効かせ、連続記事処理時のコストを削減

ベトナム語の長文記事でも数百〜数千トークン程度で処理でき、Haiku なら極めて安価です。

## 既知の制限 (MVP)

- 表示は最新 50 件のみ (ページネーションなし)
- 本文抽出 (trafilatura) はサイトのHTML構造に依存。失敗時はRSSのsummaryをフォールバックに使用
- 翻訳に失敗した記事はスキップして保存しない
- 記事のソースサイトのレート制限に注意 (短時間で連続取得しすぎない)
- 認証なし。ローカル起動を想定

## トラブルシュート

- **記事が出てこない**: ログに `Fetched N new articles from ...` が出ているか確認。`ANTHROPIC_API_KEY` の設定漏れがあると翻訳が全部失敗します
- **スケジューラが二重起動する**: 別プロセスで `python app.py` を多重起動していないか確認 (Flask の reloader は無効化済み)
- **本文が短い**: trafilatura が抽出に失敗しているケース。RSSのsummaryで翻訳されているはずなので一覧では問題なし、詳細で原文が短く見えます
