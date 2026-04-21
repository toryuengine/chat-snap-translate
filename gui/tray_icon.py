"""タスクトレイ常駐アイコン (pystray)"""
import pystray
from PIL import Image, ImageDraw


def _make_icon() -> Image.Image:
    """シンプルなアイコン画像を生成（64×64 RGBA）"""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, size - 2, size - 2], fill="#1a6bc5")  # 青い円
    d.rectangle([16, 18, 48, 24], fill="white")             # "T" 横棒
    d.rectangle([28, 24, 36, 48], fill="white")             # "T" 縦棒
    return img


class TrayIcon:
    def __init__(self, config, overlay, hotkey_manager, root) -> None:
        self.config = config
        self.overlay = overlay
        self.hotkey_manager = hotkey_manager
        self.root = root
        self._icon: pystray.Icon | None = None

    def run(self) -> None:
        """pystray のイベントループを開始する（デーモンスレッドで呼ぶこと）"""
        menu = pystray.Menu(
            pystray.MenuItem("設定を開く", self._open_settings),
            pystray.MenuItem("キャプチャエリアを再設定", self._reconfigure_capture),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("終了", self._quit),
        )
        tooltip = f"ゲームチャット翻訳  [{self.config.hotkey.upper()}]"
        self._icon = pystray.Icon("game_chat_translator", _make_icon(), tooltip, menu)
        self._icon.run()

    # ------------------------------------------------------------------ #
    # メニューハンドラ（pystray スレッド → root.after で UI スレッドに委譲）
    # ------------------------------------------------------------------ #

    def _open_settings(self, icon, item) -> None:
        self.root.after(0, self._show_settings)

    def _reconfigure_capture(self, icon, item) -> None:
        self.root.after(0, self._show_capture_selector)

    def _quit(self, icon, item) -> None:
        self.hotkey_manager.unbind()
        icon.stop()
        self.root.after(0, self.root.quit)

    # ------------------------------------------------------------------ #

    def _show_settings(self) -> None:
        from gui.settings_window import SettingsWindow
        SettingsWindow(self.root, self.config, self.hotkey_manager)

    def _show_capture_selector(self) -> None:
        from gui.capture_selector import CaptureSelector
        CaptureSelector(self.root, self.config)
