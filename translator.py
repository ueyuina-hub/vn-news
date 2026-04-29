import json
import logging
import os
import re

from anthropic import Anthropic

from config import CLAUDE_MODEL, MAX_BODY_CHARS, VALID_CATEGORIES

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


SYSTEM_PROMPT = """あなたはベトナムのニュース記事を日本人読者向けに日本語化する編集者です。
入力として、ベトナム語(または英語)のニュース記事のタイトルと本文がXMLタグで与えられます。
以下のすべてのタスクをまとめて行い、結果を1つのJSONで返してください。

タスク:
1. title_ja: タイトルを自然で読みやすい日本語にする
2. body_ja: 本文を読みやすい日本語に翻訳する。改行は適度に保つ
3. summary_ja: 本文の要点を日本語で3行に要約する。配列で3要素を返す
4. category: 次の5つから記事内容に最も近いものを1つ選ぶ — 政治 / 経済 / 社会 / 観光 / 国際

カテゴリ判定の指針:
- 政治: 政府、政策、選挙、外交、法律、党の動き
- 経済: 株価、為替、企業業績、貿易、産業、不動産
- 社会: 事件事故、教育、医療、環境、文化、生活、犯罪
- 観光: 旅行、観光地、ホテル、グルメ、レジャー
- 国際: ベトナム以外の国の出来事、国際情勢全般

出力形式: 必ず<json>...</json>タグで囲んだJSONのみを返してください。前置きや解説は不要です。
JSONのキーは title_ja, body_ja, summary_ja, category の4つだけです。"""


def _truncate(text: str, limit: int) -> str:
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit] + "...(truncated)"


def _extract_json(text: str) -> dict:
    match = re.search(r"<json>(.*?)</json>", text, re.DOTALL)
    raw = match.group(1).strip() if match else text.strip()
    # Strip optional code fences
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
    return json.loads(raw)


def translate_article(title_vi: str, body_vi: str) -> dict:
    """Translate, summarize, and categorize an article in a single Claude call.

    Returns dict with keys: title_ja, body_ja, summary_ja (str, newline-joined), category.
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
        logger.warning("Invalid category %r, falling back to 社会", category)
        category = "社会"

    if not title_ja or not body_ja or not summary_lines:
        raise ValueError("Claude response missing required fields")

    return {
        "title_ja": title_ja,
        "body_ja": body_ja,
        "summary_ja": "\n".join(summary_lines),
        "category": category,
    }
