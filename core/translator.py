"""OCR + 翻訳モジュール — OpenAI / Anthropic 両対応"""
import json

# プロバイダー共通のシステムプロンプト
_SYSTEM_PROMPT = """\
You are an OCR and translation assistant for game chat screenshots.

Instructions:
1. Extract ALL visible text lines from the provided image.
2. For each line, identify its language.
3. Translate non-Japanese text into natural Japanese.
4. Return Japanese text as-is (no translation needed).
5. Return ONLY a JSON object — no markdown fences, no extra explanation.

Response format:
{
  "lines": [
    {
      "original": "<original text>",
      "language": "<ISO 639-1 code, e.g. en, zh, ko>",
      "translation": "<Japanese translation, or same as original if already Japanese>"
    }
  ]
}

If no text is detected, return: {"lines": []}
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
