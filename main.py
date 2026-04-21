"""
ゲームチャット翻訳ツール — エントリーポイント

起動フロー:
  1. 設定読み込み (core.config)
  2. tkinter 初期化（メインウィンドウは非表示）
  3. .env 未設定なら API キー設定ガイドを表示 (gui.setup_wizard)
  4. キャプチャエリア選択（毎回）
  5. グローバルホットキーバインド (gui.hotkey_manager)
  6. タスクトレイアイコンをデーモンスレッドで起動 (gui.tray_icon)
  7. tkinter メインループ（イベント待機）
"""

import sys
import threading
import tkinter as tk

from core.config import Config
from gui.hotkey_manager import HotkeyManager
from gui.overlay import OverlayWindow
from gui.tray_icon import TrayIcon


def main() -> None:
    config = Config()

    # --- tkinter 初期化（メインウィンドウは非表示で常駐） ---
    root = tk.Tk()
    root.withdraw()
    root.title("ゲームチャット翻訳")

    # Windows: タスクバーにメインウィンドウのボタンを出さない
    try:
        root.wm_attributes("-toolwindow", True)
    except tk.TclError:
        pass

    # --- オーバーレイウィンドウ（初期状態は非表示） ---
    overlay = OverlayWindow(root, config)

    # --- .env チェック（APIキー未設定なら設定ガイドを表示） ---
    if not config.is_env_ready():
        from gui.setup_wizard import SetupWizard
        wizard = SetupWizard(root, config)
        root.wait_window(wizard.window)

        if not config.is_env_ready():
            root.quit()
            sys.exit(0)

    # --- キャプチャエリア選択（起動のたびに毎回実施） ---
    from gui.capture_selector import CaptureSelector
    selector = CaptureSelector(root, config)
    root.wait_window(selector.window)

    if not config.capture_area:
        # Esc でキャンセルされた場合は終了
        root.quit()
        sys.exit(0)

    # --- グローバルホットキーバインド ---
    hotkey_manager = HotkeyManager(config, overlay)
    try:
        hotkey_manager.bind()
        print(f"[INFO] ホットキー '{config.hotkey}' をバインドしました。")
    except Exception as e:
        print(f"[WARNING] ホットキーのバインドに失敗しました: {e}")

    # --- タスクトレイアイコン（デーモンスレッドで起動） ---
    tray = TrayIcon(config, overlay, hotkey_manager, root)
    threading.Thread(target=tray.run, daemon=True).start()

    print("[INFO] 待機中... タスクトレイアイコンを右クリックして終了できます。")

    root.mainloop()


if __name__ == "__main__":
    main()
