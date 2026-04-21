"""スクリーンキャプチャモジュール (mss 使用)"""
import base64
import io

import mss
from PIL import Image

MAX_WIDTH = 800  # API 送信前のリサイズ上限


def capture_area(area: dict) -> tuple[Image.Image, str]:
    """
    指定エリアをキャプチャし (PIL Image, base64文字列) を返す。

    Parameters
    ----------
    area : dict
        {"x": int, "y": int, "width": int, "height": int}

    Returns
    -------
    tuple[Image.Image, str]
        PIL Image と PNG の base64 エンコード文字列のペア。
    """
    with mss.mss() as sct:
        monitor = {
            "left": area["x"],
            "top": area["y"],
            "width": area["width"],
            "height": area["height"],
        }
        shot = sct.grab(monitor)
        img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")

    # 最大幅を超える場合はアスペクト比を維持してリサイズ
    if img.width > MAX_WIDTH:
        ratio = MAX_WIDTH / img.width
        img = img.resize((MAX_WIDTH, int(img.height * ratio)), Image.LANCZOS)

    # PNG → base64
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    return img, img_b64
