import json
import logging
import os
import re

from anthropic import Anthropic

from config import CLAUDE_MODEL, MAX_BODY_CHARS, VALID_CATEGORIES, VALID_IMPORTANCE

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        _client = Anthropic(api_key=api_key)
    return _client


SYSTEM_PROMPT = """あなたはベトナムでサウナ・温浴事業を展開する日本企業の社長専属の現地ニュース編集者です。
入力としてベトナム語(または英語)のニュース記事のタイトルと本文がXMLタグで与えられます。

【最重要・文体方針】
社長や社員、家族みんなが理解できるよう、「こども新聞」のように **わかりやすい日本語** で書いてください:
- 専門用語・外来語・略語は、初出で必ずカッコで一言補足する
  例: 「VND(ベトナムの通貨)」「外資(外国の会社)」「不動産投資信託(複数の人でビルを買う仕組み)」
- 1文は短く(40字以内が目安)。長い文は2〜3文に分ける
- 受け身や難しい言い回しは避け、主語と述語をはっきりさせる
- 数字には単位を必ず付け、必要なら円換算もカッコで添える(例: 約100億ドン(約60万円))
- 原意は絶対に変えないが、「平易な言葉に置き換えて伝える」意識で

以下のすべてを行い、結果を1つのJSONで返してください:

1. title_ja: タイトルをわかりやすい日本語にする(原意は保つ。難語があれば言い換える)
2. body_ja: 本文を「こども新聞」スタイルでわかりやすく翻訳する。
   改行は適度に保ち、難しい用語は最初の登場時にカッコで補足する。
3. summary_ja: 本文の要点を3行に要約する。配列で3要素。1行40〜60字。やさしい言葉で。
4. category: 次の8カテゴリから最も適切なものを1つだけ選ぶ
   - 不動産 / 観光 / 経済 / 規制・法律 / 為替・金融 / サウナ・ウェルネス / リスク情報 / その他
5. importance: 経営判断にどの程度影響するかを 1〜3 の整数で評価する
   - 3 = 高: 事業判断や投資判断に直結しうる(法改正、外資規制、為替急変、観光需要の急変、現地の重大事件など)
   - 2 = 中: 押さえておきたい参考情報(市場トレンド、業界動向、富裕層の消費動向など)
   - 1 = 低: 一般的なニュース、雑報
6. exec_comment: 経営者にとって「なぜ重要か」を日本語1〜2文(目安60〜100字)で、
   やさしい言葉で説明する。サウナ事業・不動産・観光・外資規制・為替・治安・富裕層消費との
   接点があれば必ず触れる。接点が薄い記事では、その旨を率直に書いてよい
   (例: "直接の事業への影響は小さいですが、現地の人がどんなものにお金を使っているかを知る材料になります")。

カテゴリ判定の指針(社長の関心軸):
- 不動産: ベトナムの不動産市場、ホテル・リゾート開発、商業施設、土地法
- 観光: 観光客数、航空便、ビザ、観光地、ホテル稼働率、旅行支出
- 経済: 株価、企業業績、貿易、産業全般、消費動向、富裕層の動向
- 規制・法律: 外資規制、業法、許認可、税制、労働法、新法成立
- 為替・金融: VND為替、銀行、金利、インフレ、物価
- サウナ・ウェルネス: サウナ、温浴、スパ、フィットネス、ウェルネス施設、健康消費
- リスク情報: 治安、事故、自然災害、政情不安、感染症、デモ、汚職事件
- その他: 上記に当てはまらないもの

出力形式: 必ず<json>...</json>タグで囲んだJSONのみを返してください。前置きや解説は不要です。
JSONのキーは title_ja, body_ja, summary_ja, category, importance, exec_comment の6つだけです。
summary_ja は文字列の配列、importance は整数、それ以外は文字列です。"""


def _truncate(text: str, limit: int) -> str:
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit] + "...(truncated)"


def _extract_json(text: str) -> dict:
    match = re.search(r"<json>(.*?)</json>", text, re.DOTALL)
    raw = match.group(1).strip() if match else text.strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
    return json.loads(raw)


def translate_article(title_vi: str, body_vi: str) -> dict:
    """Translate, summarize, categorize, and rate importance in a single Claude call.

    Returns dict with keys:
      title_ja, body_ja, summary_ja (newline-joined), category, importance, exec_comment
    Raises on unrecoverable API errors.
    """
    client = _get_client()
    body_trimmed = _truncate(body_vi or "", MAX_BODY_CHARS)
    user_text = f"<title>{title_vi or ''}</title>\n<body>{body_trimmed}</body>"

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_text}],
    )

    text_parts = [b.text for b in response.content if getattr(b, "type", None) == "text"]
    raw_text = "".join(text_parts)

    try:
        data = _extract_json(raw_text)
    except (json.JSONDecodeError, AttributeError) as e:
        logger.error("Failed to parse Claude JSON: %s\nRaw: %s", e, raw_text[:500])
        raise

    title_ja = (data.get("title_ja") or "").strip()
    body_ja = (data.get("body_ja") or "").strip()
    summary = data.get("summary_ja") or []
    if isinstance(summary, str):
        summary_lines = [s for s in summary.split("\n") if s.strip()][:3]
    else:
        summary_lines = [str(s).strip() for s in summary if str(s).strip()][:3]

    category = (data.get("category") or "").strip()
    if category not in VALID_CATEGORIES:
        logger.warning("Invalid category %r, falling back to その他", category)
        category = "その他"

    try:
        importance = int(data.get("importance") or 1)
    except (TypeError, ValueError):
        importance = 1
    if importance not in VALID_IMPORTANCE:
        importance = max(1, min(3, importance))

    exec_comment = (data.get("exec_comment") or "").strip()

    if not title_ja or not body_ja or not summary_lines:
        raise ValueError("Claude response missing required fields")

    return {
        "title_ja": title_ja,
        "body_ja": body_ja,
        "summary_ja": "\n".join(summary_lines),
        "category": category,
        "importance": importance,
        "exec_comment": exec_comment,
    }
