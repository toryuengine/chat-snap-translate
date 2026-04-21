"""ドラッグ操作によるキャプチャエリア選択 UI"""
import tkinter as tk
from typing import Callable

import mss


class CaptureSelector:
    """
    全画面の半透明暗転オーバーレイ上でドラッグによりキャプチャ矩形を選択する。

    スクリーンショット撮影は行わず、wm_attributes("-alpha") による半透明ウィンドウを使用。
    これにより canvas のマウスイベントが確実に届く。

    選択完了時: config.capture_area を更新 → config.save() → on_done コールバック呼び出し
    Esc キャンセル時: on_done は呼ばれない（ウィンドウを破棄するだけ）
    """

    def __init__(
        self,
        root: tk.Tk,
        config,
        on_done: Callable[[dict], None] | None = None,
    ) -> None:
        self.root = root
        self.config = config
        self.on_done = on_done

        self._rect_id: int | None = None
        self._size_id: int | None = None
        self._start_x = 0
        self._start_y = 0
        self._offset_x = 0
        self._offset_y = 0

        self._open()

    def _open(self) -> None:
        # mss で仮想スクリーン全体のサイズとオフセットだけ取得（撮影はしない）
        with mss.mss() as sct:
            mon = sct.monitors[0]  # 全モニタ結合仮想スクリーン
            self._offset_x = mon["left"]
            self._offset_y = mon["top"]
            screen_w = mon["width"]
            screen_h = mon["height"]

        self.window = tk.Toplevel(self.root)
        self.window.overrideredirect(True)
        self.window.wm_attributes("-topmost", True)
        self.window.wm_attributes("-alpha", 0.35)   # 半透明暗転（35% 不透明）
        self.window.configure(bg="#000000")
        self.window.geometry(f"{screen_w}x{screen_h}+{self._offset_x}+{self._offset_y}")

        self.canvas = tk.Canvas(
            self.window,
            bg="#000000",
            highlightthickness=0,
            cursor="crosshair",
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 操作説明テキスト
        self.canvas.create_text(
            screen_w // 2, 50,
            text="チャットエリアをドラッグで選択してください  (Esc でキャンセル)",
            fill="white",
            font=("Segoe UI", 16),
        )

        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.window.bind("<Escape>", lambda _: self.window.destroy())

        # フォーカスとマウスキャプチャを確実に取得
        self.window.update()
        self.window.focus_force()
        self.window.grab_set()

    # ------------------------------------------------------------------ #

    def _on_press(self, event: tk.Event) -> None:
        self._start_x = event.x
        self._start_y = event.y
        self._clear_rect()

    def _on_drag(self, event: tk.Event) -> None:
        self._clear_rect()

        x0, y0 = self._start_x, self._start_y
        x1, y1 = event.x, event.y

        # 選択矩形
        self._rect_id = self.canvas.create_rectangle(
            x0, y0, x1, y1,
            outline="#4a9eff",
            width=2,
            fill="#4a9eff",
            stipple="gray12",   # 選択エリアをわずかに明るく
        )

        # サイズ表示
        w, h = abs(x1 - x0), abs(y1 - y0)
        lx = max(x0, x1) + 6
        ly = max(y0, y1) + 6
        self._size_id = self.canvas.create_text(
            lx, ly,
            text=f"{w} × {h} px",
            fill="white",
            font=("Segoe UI", 11, "bold"),
            anchor="nw",
        )

    def _on_release(self, event: tk.Event) -> None:
        x1 = min(self._start_x, event.x) + self._offset_x
        y1 = min(self._start_y, event.y) + self._offset_y
        x2 = max(self._start_x, event.x) + self._offset_x
        y2 = max(self._start_y, event.y) + self._offset_y

        w, h = x2 - x1, y2 - y1
        if w < 10 or h < 10:
            return  # 小さすぎる選択は無視

        area = {"x": x1, "y": y1, "width": w, "height": h}
        self.config.set("capture_area", area)
        self.config.save()
        self.window.destroy()

        if self.on_done:
            self.on_done(area)

    def _clear_rect(self) -> None:
        if self._rect_id is not None:
            self.canvas.delete(self._rect_id)
            self._rect_id = None
        if self._size_id is not None:
            self.canvas.delete(self._size_id)
            self._size_id = None
