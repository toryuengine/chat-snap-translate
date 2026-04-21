"""グローバルホットキー管理・翻訳ワークフロー制御"""
import threading
import time

import keyboard

from core.capture import capture_area
from core.translator import translate_image


class HotkeyManager:
    """
    グローバルホットキーをバインドし、押下時にキャプチャ → 翻訳 → 表示を実行する。

    翻訳処理中に再度ホットキーが押された場合、前の処理をキャンセルして新たに実行する。
    """

    def __init__(self, config, overlay) -> None:
        self.config = config
        self.overlay = overlay

        self._worker: threading.Thread | None = None
        self._cancel_event = threading.Event()
        self._bound = False

    # ------------------------------------------------------------------ #
    # バインド / アンバインド
    # ------------------------------------------------------------------ #

    def bind(self) -> None:
        if self._bound:
            return
        keyboard.add_hotkey(self.config.hotkey, self._on_hotkey, suppress=False)
        self._bound = True

    def unbind(self) -> None:
        keyboard.unhook_all_hotkeys()
        self._bound = False

    def rebind(self, new_hotkey: str) -> None:
        """ホットキーを変更して即時再バインドする"""
        self.unbind()
        self.config.set("hotkey", new_hotkey)
        self.config.save()
        self.bind()

    # ------------------------------------------------------------------ #
    # ホットキー押下ハンドラ（keyboard ライブラリの内部スレッドから呼ばれる）
    # ------------------------------------------------------------------ #

    def _on_hotkey(self) -> None:
        if self._worker and self._worker.is_alive():
            self._cancel_event.set()
            self._worker.join(timeout=0.2)

        self._cancel_event.clear()
        self._worker = threading.Thread(target=self._process, daemon=True)
        self._worker.start()

    # ------------------------------------------------------------------ #
    # 翻訳ワーカー（別スレッドで実行）
    # ------------------------------------------------------------------ #

    def _process(self) -> None:
        t_start = time.monotonic()

        if not self.config.capture_area:
            self.overlay.show_error("キャプチャエリアが設定されていません")
            return
        if not self.config.active_api_key:
            self.overlay.show_error(".env に API キーが設定されていません")
            return

        self.overlay.show_loading()

        # --- スクリーンキャプチャ ---
        try:
            _, img_b64 = capture_area(self.config.capture_area)
        except Exception as e:
            if not self._cancel_event.is_set():
                self.overlay.show_error(f"キャプチャ失敗: {e}")
            return

        elapsed_ms = (time.monotonic() - t_start) * 1000
        if elapsed_ms > 200:
            print(f"[WARNING] キャプチャに {elapsed_ms:.0f}ms かかりました（目標: 200ms 以内）")

        if self._cancel_event.is_set():
            return

        # --- OCR + 翻訳 ---
        try:
            lines = translate_image(
                provider=self.config.api_provider,
                api_key=self.config.active_api_key,
                model=self.config.active_model,
                image_b64=img_b64,
                timeout=8.0,
            )
        except Exception as e:
            if not self._cancel_event.is_set():
                msg = str(e)
                if len(msg) > 80:
                    msg = msg[:77] + "..."
                self.overlay.show_error(f"翻訳失敗: {msg}")
            return

        if self._cancel_event.is_set():
            return

        self.overlay.show_result(lines)
