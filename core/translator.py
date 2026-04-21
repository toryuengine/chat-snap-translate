"""OCR + 翻訳モジュール — OpenAI / Anthropic 両対応"""
import json

# プロバイダー共通のシステムプロンプト
_SYSTEM_PROMPT = """\
あなたはゲームチャット画面の OCR・翻訳アシスタントです。
提供された画像からチャットテキストをすべて読み取り、以下のルールに従って処理してください。

【翻訳ルール】
- 英語・中国語・韓国語・その他すべての言語を自然な日本語に翻訳する
- 日本語のテキストはそのまま出力する（翻訳不要）
- ゲーム用語・スラング・略語は原文をそのまま残し、括弧内に意味を補足する
  例）"GG" → "GG（お疲れ様）"、"gg ez" → "gg ez（楽勝だった）"

【発言者の表記ルール】
- チャット行に「ニックネーム」と「発言内容」が含まれる場合、translation フィールドを以下の形式で出力する
  形式）名前：発言内容の日本語訳
  例）"PlayerOne: nice shot!" → "PlayerOne：ナイスショット！"
- ニックネームは翻訳せずそのまま維持する

【除外ルール】
- 空行・UIラベル（"All" "Team" "System" などのタブ・ラベル文字）は出力しない

【出力ルール】
- 必ず JSON 形式のみで返す。前置き・説明文・コードブロック記号は不要

出力形式:
{
  "lines": [
    {
      "original": "元のテキスト",
      "language": "言語コード（en / ko / zh / ja など）",
      "translation": "日本語訳（発言者がいる場合は 名前：発言内容）"
    }
  ]
}
"""


def translate_image(
    provider: str,
    api_key: str,
    model: str,
    image_b64: str,
    timeout: float = 8.0,
) -> list[dict]:
    """
    キャプチャ画像を OCR + 翻訳し、行リストを返す。

    Parameters
    ----------
    provider : str
        "openai" または "anthropic"
    api_key : str
        プロバイダーの API キー
    model : str
        使用モデル名
    image_b64 : str
        PNG の base64 エンコード文字列
    timeout : float
        タイムアウト秒数（デフォルト 8 秒）

    Returns
    -------
    list[dict]
        [{"original": str, "language": str, "translation": str}, ...]
    """
    if provider == "anthropic":
        return _translate_anthropic(api_key, model, image_b64, timeout)
    elif provider == "openai":
        return _translate_openai(api_key, model, image_b64, timeout)
    else:
        raise ValueError(f"未対応のプロバイダー: '{provider}'  (.env の API_PROVIDER を確認してください)")


# ------------------------------------------------------------------ #
# OpenAI (GPT-4o など vision 対応モデル)
# ------------------------------------------------------------------ #

def _translate_openai(api_key: str, model: str, image_b64: str, timeout: float) -> list[dict]:
    from openai import OpenAI

    client = OpenAI(api_key=api_key, timeout=timeout)

    response = client.chat.completions.create(
        model=model,
        max_tokens=1024,
        response_format={"type": "json_object"},  # JSON モード（構文エラーを防止）
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                    },
                    {
                        "type": "text",
                        "text": "Extract and translate all chat text in this image.",
                    },
                ],
            },
        ],
    )

    raw = response.choices[0].message.content.strip()
    data = json.loads(raw)
    return data.get("lines", [])


# ------------------------------------------------------------------ #
# Anthropic (Claude — プロンプトキャッシュ有効)
# ------------------------------------------------------------------ #

def _translate_anthropic(api_key: str, model: str, image_b64: str, timeout: float) -> list[dict]:
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model=model,
        max_tokens=1024,
        timeout=timeout,
        system=[
            {
                "type": "text",
                "text": _SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},  # プロンプトキャッシュ有効化
            }
        ],
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Extract and translate all chat text in this image.",
                    },
                ],
            }
        ],
    )

    raw = message.content[0].text.strip()

    # マークダウンコードブロックが混入した場合に除去
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1].lstrip("json").strip() if len(parts) > 1 else raw

    data = json.loads(raw)
    return data.get("lines", [])
