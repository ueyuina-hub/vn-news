# Vietnam Briefing — ベトナム現地ニュース日本語版

ベトナムでサウナ・温浴事業を展開する経営者向けに、ベトナム現地ニュースのRSSを定期取得し、Claude API で日本語に翻訳・3行要約・カテゴリ分類・重要度判定・経営視点コメントを付与して表示する Flask Web アプリです。

毎朝スマホで通勤中に確認することを想定し、シンプルで高級感のあるUIにしています。

## 主な機能

- **RSS 定期取得** (VnExpress / Tuoi Tre / Thanh Nien など主要紙)
- **Claude API による翻訳・3行要約・カテゴリ分類・重要度判定**(1リクエストでまとめて処理)
- **経営者向けコメント** — 各記事に「なぜ重要か」を1文で添付
- **重要度3段階** — 高(赤) / 中(黄) / 低
- **本日の重要ニュース3本** をトップに自動抽出
- **キーワード検索** — タイトル・本文・要約・経営視点コメントを横断
- **カテゴリ絞り込み** — 不動産 / 観光 / 経済 / 規制・法律 / 為替・金融 / サウナ・ウェルネス / リスク情報 / その他
- **ブックマーク機能** — 一覧の☆で1クリック保存、`?bookmarked=1` で保存記事のみ表示
- **既読管理** — 詳細を開くと自動で既読化。一覧では既読は薄く表示、`?unread=1` で未読のみ表示
- **重複排除** — 同じURLの記事は2度保存しない
- **スマホ最適化** — モバイル想定の縦長レイアウト、ダークモード対応
- **サンプルデータ投入スクリプト** — APIキー無しでもUI確認可能

## ファイル構成

```
vn-news/
├── app.py            # Flask本体 + ルーティング + APScheduler + 軽量マイグレーション
├── config.py         # RSSフィード、取得間隔、カテゴリ、重要度
├── db.py             # SQLAlchemy 初期化
├── models.py         # Article モデル(importance, exec_comment 含む)
├── fetcher.py        # RSS取得 + 本文抽出 + 重複チェック + 保存
├── translator.py     # Claude API クライアント(経営者向けプロンプト)
├── seed_sample.py    # サンプル記事を投入(APIキー不要で動作確認用)
├── templates/
│   ├── base.html
│   ├── index.html    # 一覧 + 重要ニュース3本 + 検索 + カテゴリ絞り込み
│   └── detail.html   # 詳細(原文/翻訳/要約/経営視点コメント)
├── static/
│   └── style.css     # 高級感のあるエグゼクティブテーマ
├── .env.example
├── requirements.txt
└── README.md
```

## セットアップ手順

### 0. 前提

- Python 3.10 以上
- macOS / Linux / WSL を想定

### 1. プロジェクトディレクトリへ移動

```bash
cd vn-news
```

### 2. 仮想環境の作成と有効化

```bash
python3 -m venv .venv
source .venv/bin/activate
```

(Windows コマンドプロンプトの場合は `.venv\Scripts\activate`)

### 3. 依存パッケージのインストール

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. `.env` ファイルの作成

```bash
cp .env.example .env
```

`.env` を開き、`ANTHROPIC_API_KEY` に Claude API キーを設定します。
キーは [Anthropic Console](https://console.anthropic.com/) で発行できます。

```env
ANTHROPIC_API_KEY=sk-ant-...
```

### 5a. (任意) サンプルデータで動作確認

API キーを設定しなくても、サンプル6件を投入してUIだけ先に確認できます:

```bash
python seed_sample.py            # サンプル投入
python seed_sample.py --reset    # 既存記事を全削除して投入し直す
```

### 5b. 起動

```bash
python app.py
```

ブラウザで <http://localhost:8000> を開きます(ポートは `PORT` 環境変数で変更可)。

- 起動直後にバックグラウンドで **1回 即時 RSS 取得** が走ります
- 以降、`FETCH_INTERVAL_MINUTES` 分ごと(既定 30 分)に自動取得
- 初回はフィード × 最大10件を翻訳するため数分かかります

### 手動で再取得したいとき

```bash
curl -X POST http://localhost:8000/fetch
```

レスポンスは即座に `202` を返し、取得処理はバックグラウンドで続きます。

## 設定項目 (`.env`)

| 変数 | 既定値 | 説明 |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | (必須) | Claude API キー |
| `FETCH_INTERVAL_MINUTES` | `30` | RSS取得間隔(分) |
| `MAX_ARTICLES_PER_FEED` | `10` | 1フィード/1回あたりの処理上限 |
| `CLAUDE_MODEL` | `claude-haiku-4-5-20251001` | 使用モデル |
| `DB_PATH` | `vn_news.db` | SQLite DB ファイルパス |
| `PORT` | `8000` | リッスンポート |
| `DISABLE_SCHEDULER` | (未設定) | `1` で自動取得を無効化 |

## カテゴリと重要度

**カテゴリ(8種)**: 不動産 / 観光 / 経済 / 規制・法律 / 為替・金融 / サウナ・ウェルネス / リスク情報 / その他

**重要度**:

- **高(3)** — 法改正、外資規制、為替急変、観光需要の急変など、経営判断に直結
- **中(2)** — 押さえておきたい市場・業界トレンド、富裕層の動向
- **低(1)** — 一般的な雑報

## 経営視点コメントについて

各記事には Claude が「なぜ重要か」を1文(50〜90字目安)で生成します。
サウナ事業 / 不動産 / 観光 / 外資規制 / 為替 / 治安 / 富裕層消費 のいずれかとの接点を必ず探すようプロンプトで指示しています。

## 主要画面

- **トップ `/`** — 本日の重要ニュース3本 → 検索/カテゴリ → 最新一覧80件
- **詳細 `/article/<id>`** — 経営視点コメント / 3行要約 / 日本語訳 / 原文(折りたたみ)
- **手動取得 `/fetch`** — POST/GET でバックグラウンド再取得をトリガ
- **ヘルスチェック `/healthz`**

## DBスキーマ移行(古いDBを使い続ける場合)

カテゴリと項目を変更したため、以前のバージョンで作った `vn_news.db` を使い続ける場合、起動時に自動で次のカラムが追加されます(SQLite のみ):

- `importance` / `exec_comment` (経営者向け項目)
- `is_bookmarked` / `is_read` / `read_at` (ブックマーク・既読管理)

過去の記事は古いカテゴリのまま残るので、すっきり見せたい場合は次のいずれか:

```bash
rm vn_news.db                      # 全消し(推奨)
# あるいは
python seed_sample.py --reset      # クリアしてサンプルだけ表示
```

## Render に無料デプロイして知人に共有する

**ゴール**: URL ひとつ送れば知人がスマホで毎朝チェックできる状態に、月額0円で持っていく。

このリポジトリには `render.yaml` (Render Blueprint) が含まれており、
Web サービス + PostgreSQL を **Free プラン** で一括プロビジョニングできます。
共有用の **ベーシック認証** にも対応(`BASIC_AUTH_USER` / `BASIC_AUTH_PASS` をセットすれば自動で有効)。

### 構成と料金

| 項目 | プラン | 料金 |
| --- | --- | --- |
| Web service (Flask) | Render Free | **$0** |
| PostgreSQL | Render Free | **$0** (※90日制限あり、後述) |
| Claude API (Haiku 4.5) | 従量 | 月100記事で **数十円〜数百円** |

### 1. リポジトリを GitHub に push

```bash
cd vn-news
git init                                                # 済みならスキップ
git add .
git commit -m "Initial deploy"
gh repo create vn-news --private --source=. --push      # gh CLI 使用例(privateで作成)
```

(GitHubに置きたくない場合は GitLab / Bitbucket でも可)

### 2. Render で Blueprint デプロイ

1. [Render](https://render.com) にログイン(無料)
2. 「**New → Blueprint**」を選択
3. push した GitHub リポジトリを選び **Apply**
4. `render.yaml` が読み込まれ、Web サービスと PostgreSQL が自動作成される

### 3. 環境変数(シークレット)を設定

Render ダッシュボード → `vn-news` サービス → **Environment** で次の3つを追加:

| 変数 | 値 |
| --- | --- |
| `ANTHROPIC_API_KEY` | `sk-ant-...` (自分のキー、知人には渡さない) |
| `BASIC_AUTH_USER` | 任意のユーザー名 (例: `boss`) |
| `BASIC_AUTH_PASS` | 任意のパスワード (例: `vnsauna2026`) |

**Save Changes** で自動再デプロイされます。

> ベーシック認証は `BASIC_AUTH_USER` と `BASIC_AUTH_PASS` の **両方** がセットされた時だけ有効。
> 片方だけ、または未設定なら誰でもアクセスできるので注意。

### 4. 動作確認 → 知人にURLを共有

- `https://vn-news-XXXX.onrender.com/healthz` で `{"status":"ok"}` が返れば起動OK
- トップにアクセスすると認証ダイアログが出るので、上で決めたユーザー/パスでログイン
- 起動直後にバックグラウンドで RSS 取得が走り、数分で記事が並び始める

知人に送るのは次の3つだけ:

```
🇻🇳 Vietnam Briefing
URL : https://vn-news-XXXX.onrender.com/
ID  : boss
PW  : vnsauna2026
```

ホーム画面に追加すれば「アプリのように」使えます。

### Free プランの制約と回避策

#### スリープ問題
- 無料Webサービスは **15分アクセスが無いとスリープ** し、次回起動に30秒〜1分かかります
- 知人が朝1回見るくらいなら気にならないレベル
- 確実にスケジューラを動かしたいなら無料の外部cron (UptimeRobot等) で `/healthz` を15分おきに叩くのが定番

#### **PostgreSQL 90日制限(重要)**
- Render Free PostgreSQL は **作成から90日で自動削除** されます
- 対策: 90日経つ前に **Neon** など別の無料Postgresに移行する(既読・ブックマークも維持できる)
  1. [Neon](https://neon.tech) で無料アカウント作成 → DB作成 → 接続文字列(`postgresql://...`)をコピー
  2. Render ダッシュボード → `vn-news` → Environment → `DATABASE_URL` を Neon のものに上書き
  3. **Save Changes** で再デプロイ
  4. 不要になった `vn-news-db` (Render Postgres) は削除してOK

> Neon Free は 0.5GB / 1ブランチ / 永続(削除されない)。本アプリのデータ量なら数年は余裕で持ちます。

#### 既読・ブックマークを永続させたい場合
- 上記の Neon 移行を最初からやっておくと安全
- どうしてもデータが消えても困らないなら Render Free Postgres のままで、90日ごとに作り直しでも運用可

### サブディレクトリ構成について

リポジトリのルートが `vn-news/` の **親** (モノレポ)である場合、`render.yaml` の `rootDir: vn-news` が効きます。
リポジトリ直下が `vn-news/` の中身そのものなら、`render.yaml` の `rootDir` 行を削除してください。

### よくあるトラブル

- **`ANTHROPIC_API_KEY is not set`** — ステップ3で設定漏れ。Environment タブを確認
- **認証ダイアログが出ない** — `BASIC_AUTH_USER` または `_PASS` の片方が空。両方セットすること
- **`SSL: decryption failed or bad record mac`** — psycopg2 のスレッド共有問題。`app.py` で `NullPool` を使うよう既に対応済み
- **記事が増えない** — Freeプランはスリープ中 APScheduler が止まる。UptimeRobot で `/healthz` を定期pingするか、知人がアクセスするたびに起動時取得が走るので実用上は問題なし
- **初回が遅い** — Freeプランのコールドスタート。30秒〜1分待つ

## 利用モデル / コスト

- **claude-haiku-4-5-20251001** (Haiku 4.5) を使用
- 1記事あたり 1リクエストで「翻訳 + 3行要約 + カテゴリ分類 + 重要度 + 経営コメント」をまとめて生成
- システムプロンプトに prompt caching を効かせ、連続処理時のコストを削減

## 既知の制限 (MVP)

- 表示は最新 80 件まで(ページネーションなし)
- 本文抽出 (trafilatura) はサイトのHTML構造に依存。失敗時はRSSのsummaryをフォールバック
- 翻訳に失敗した記事はスキップして保存しない
- 認証なし(ローカル/個人利用想定)
- レート制限に注意(短時間で連続取得しすぎない)

## トラブルシュート

- **記事が出てこない** — ログに `Fetched N new articles from ...` が出ているか確認。`ANTHROPIC_API_KEY` の設定漏れがあると全記事の翻訳が失敗します。まずは `python seed_sample.py` でUI動作確認するのがおすすめ
- **`No module named ...`** — 仮想環境を有効化していない可能性。`source .venv/bin/activate` を再実行
- **`lxml` 関連でインストール失敗** — Xcode CLT が必要な場合あり: `xcode-select --install`
- **本文が極端に短い** — trafilatura の本文抽出がブロックされた可能性。RSSのsummaryで翻訳されているはず
- **ポート 8000 が使用中** — `PORT=5050 python app.py` のように変更

## 次に追加できる機能(提案)

1. **メール/LINE通知** — 重要度3の記事が出たら朝8時に1通まとめて配信
2. **PDF/メモ書き出し** — 「今日の重要ニュース3本」を1枚PDFにして経営会議に持参
3. **コメント・社内メモ機能** — 社長や役員が記事ごとにメモを残せる
4. **競合・キーワード自動アラート** — 「サウナ」「温浴」「○○ホテル」など指定語が出たら強調表示+通知
5. **ダッシュボード** — カテゴリ別の記事数推移、重要度の出現頻度をグラフ化(週次・月次)
6. **VND/JPY 為替推移ウィジェット** — 公開API連携でトップに常時表示
7. **Telegram / Slack Bot 連携** — 重要ニュースをチャットに自動投稿
8. **音声読み上げ** — 通勤中の "ながら" 用に3行要約を音声化
9. **多言語対応** — 英語版を併記して国際チームと共有
10. **過去ログ全文検索 (FTS5)** — 件数が増えたら SQLite FTS5 で高速化
11. **AI による週次/月次レポート自動生成** — 重要記事をまとめた経営サマリ
