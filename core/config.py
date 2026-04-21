"""設定管理モジュール

config.json : ホットキー・キャプチャ座標・表示設定などアプリ設定を保存
.env        : API プロバイダー・APIキー・モデル名を管理（git 除外）
"""
import json
import os
from pathlib import Path

from dotenv import load_dotenv

# core/config.py の2階層上がプロジェクトルート
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
CONFIG_PATH = PROJECT_ROOT / "config.json"

DEFAULT_CONFIG: dict = {
    "hotkey": "ctrl+shift+t",
    "capture_area": None,       # {"x": int, "y": int, "width": int, "height": int}
    "display_duration": 10,
    "opacity": 0.85,
    "window_position": {"x": None, "y": None},
}


class Config:
    def __init__(self) -> None:
        # プロジェクトルートの .env を絶対パスで読み込む
        load_dotenv(dotenv_path=ENV_PATH, override=False)
        self._data: dict = {}
        self.load()

    # ------------------------------------------------------------------ #
    # 永続化（config.json）
    # ------------------------------------------------------------------ #

    def load(self) -> None:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            self._data = {**DEFAULT_CONFIG, **loaded}
        else:
            self._data = DEFAULT_CONFIG.copy()

    def save(self) -> None:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------ #
    # 汎用アクセサ
    # ------------------------------------------------------------------ #

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value) -> None:
        self._data[key] = value

    # ------------------------------------------------------------------ #
    # .env から読み取る API 設定（read-only）
    # ------------------------------------------------------------------ #

    @property
    def api_provider(self) -> str:
        """使用プロバイダー: 'openai' または 'anthropic'"""
        return os.getenv("API_PROVIDER", "openai").lower()

    @property
    def active_api_key(self) -> str:
        """現在のプロバイダーの API キー"""
        if self.api_provider == "anthropic":
            return os.getenv("ANTHROPIC_API_KEY", "")
        return os.getenv("OPENAI_API_KEY", "")

    @property
    def active_model(self) -> str:
        """現在のプロバイダーのモデル名"""
        if self.api_provider == "anthropic":
            return os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
        return os.getenv("OPENAI_MODEL", "gpt-4o")

    # ------------------------------------------------------------------ #
    # ステータス確認
    # ------------------------------------------------------------------ #

    def is_env_ready(self) -> bool:
        """APIキーが .env に設定されているか"""
        return bool(self.active_api_key)

    def is_configured(self) -> bool:
        """起動に必要な設定が揃っているか（.env + キャプチャエリア）"""
        return self.is_env_ready() and self.capture_area is not None

    # ------------------------------------------------------------------ #
    # config.json のプロパティ
    # ------------------------------------------------------------------ #

    @property
    def hotkey(self) -> str:
        return self._data.get("hotkey", "ctrl+shift+t")

    @property
    def capture_area(self) -> dict | None:
        return self._data.get("capture_area")

    @property
    def display_duration(self) -> int:
        return self._data.get("display_duration", 10)

    @property
    def opacity(self) -> float:
        return self._data.get("opacity", 0.85)

    @property
    def window_position(self) -> dict:
        return self._data.get("window_position", {"x": None, "y": None})
