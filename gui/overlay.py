"""翻訳結果表示オーバーレイ (tkinter)"""
import tkinter as tk

# --- カラーパレット ---
BG_COLOR = "#1a1a2e"
SEP_COLOR = "#2a2a4a"
ORIG_COLOR = "#9090aa"
TRANS_COLOR = "#ffffff"
ERROR_COLOR = "#ff6666"
EMPTY_COLOR = "#666688"
FONT_FAMILY = "Segoe UI"


class OverlayWindow:
    """
    常に最前面に表示されるフレームレス半透明ウィンドウ。

    公開メソッド（任意スレッドから呼び出し可）:
        show_loading() : ローディングインジケーター表示
        show_result()  : 翻訳結果表示
        show_error()   : エラーメッセージ表示
    """

    def __init__(self, root: tk.Tk, config) -> None:
        self.root = root
        self.config = config

        self._fade_id: str | None = None
        self._loading_id: str | None = None
        self._loading_label: tk.Label | None = None
        self._loading_dot_count = 0
        self._drag_x = 0
        self._drag_y = 0

        self.window = tk.Toplevel(root)
        self._setup_window()
        self._build_layout()
        self.window.withdraw()

    # ------------------------------------------------------------------ #
    # 初期化
    # ------------------------------------------------------------------ #

    def _setup_window(self) -> None:
        w = self.window
        w.overrideredirect(True)           # フレームレス
        w.wm_attributes("-topmost", True)  # 常に最前面
        w.wm_attributes("-alpha", self.config.opacity)
        w.configure(bg=BG_COLOR)
        w.bind("<Button-1>", self._drag_start)
        w.bind("<B1-Motion>", self._drag_move)
        self._place_window()

    def _build_layout(self) -> None:
        self._outer = tk.Frame(self.window, bg=BG_COLOR, padx=12, pady=10)
        self._outer.pack(fill=tk.BOTH, expand=True)

        # 翻訳行・ローディングをまとめるコンテナ
        self._content = tk.Frame(self._outer, bg=BG_COLOR)
        self._content.pack(fill=tk.BOTH, expand=True)

    # ------------------------------------------------------------------ #
    # ウィンドウ配置
    # ------------------------------------------------------------------ #

    def _place_window(self) -> None:
        self.window.minsize(420, 0)
        pos = self.config.window_position
        if pos.get("x") is not None and pos.get("y") is not None:
            self.window.geometry(f"+{pos['x']}+{pos['y']}")
        else:
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            self.window.geometry(f"+{sw - 440}+{sh - 200}")

    def _snap_to_bottom_right(self) -> None:
        """ユーザーがドラッグしていなければ右下に吸着する"""
        # サイズを自動調整させるためリセット
        self.window.geometry("")
        self.window.update_idletasks()
        if self.config.window_position.get("x") is not None:
            return  # ユーザー指定位置を尊重
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w = max(self.window.winfo_reqwidth(), 420)
        h = self.window.winfo_reqheight()
        self.window.geometry(f"+{sw - w - 20}+{sh - h - 60}")

    # ------------------------------------------------------------------ #
    # ドラッグ移動
    # ------------------------------------------------------------------ #

    def _drag_start(self, event: tk.Event) -> None:
        self._drag_x = event.x
        self._drag_y = event.y

    def _drag_move(self, event: tk.Event) -> None:
        x = self.window.winfo_x() + event.x - self._drag_x
        y = self.window.winfo_y() + event.y - self._drag_y
        self.window.geometry(f"+{x}+{y}")
        self.config.set("window_position", {"x": x, "y": y})

    # ------------------------------------------------------------------ #
    # 公開 API（スレッドセーフ: root.after 経由で UI スレッドに委譲）
    # ------------------------------------------------------------------ #

    def show_loading(self) -> None:
        """ローディングインジケーターを表示する"""
        self.root.after(0, self._show_loading_ui)

    def show_result(self, lines: list[dict]) -> None:
        """翻訳結果を表示する"""
        self.root.after(0, lambda: self._show_result_ui(lines))

    def show_error(self, message: str) -> None:
        """エラーメッセージを表示する"""
        self.root.after(0, lambda: self._show_error_ui(message))

    # ------------------------------------------------------------------ #
    # 内部 UI 更新（UI スレッドのみ）
    # ------------------------------------------------------------------ #

    def _show_loading_ui(self) -> None:
        self._cancel_fade()
        self._clear_content()  # 前回の _loading_label も含めて破棄される

        # ローディングラベルを _content 内に新規生成
        self._loading_label = tk.Label(
            self._content,
            text="翻訳中",
            fg=ORIG_COLOR,
            bg=BG_COLOR,
            font=(FONT_FAMILY, 11),
        )
        self._loading_label.pack(anchor="w")

        self._loading_dot_count = 0
        self._animate_loading()
        self.window.deiconify()

    def _animate_loading(self) -> None:
        if self._loading_label is None:
            return  # キャンセル済み
        dots = "." * (self._loading_dot_count % 4)
        self._loading_label.config(text=f"翻訳中{dots}")
        self._loading_dot_count += 1
        self._loading_id = self.root.after(400, self._animate_loading)

    def _show_result_ui(self, lines: list[dict]) -> None:
        self._cancel_loading()
        self._clear_content()

        if not lines:
            tk.Label(
                self._content,
                text="テキストが検出されませんでした",
                fg=EMPTY_COLOR,
                bg=BG_COLOR,
                font=(FONT_FAMILY, 10),
            ).pack(anchor="w")
        else:
            for i, line in enumerate(lines[:5]):
                if i > 0:
                    tk.Frame(self._content, bg=SEP_COLOR, height=1).pack(fill=tk.X, pady=4)

                original = line.get("original", "")
                translation = line.get("translation", original)

                tk.Label(
                    self._content,
                    text=original,
                    fg=ORIG_COLOR,
                    bg=BG_COLOR,
                    font=(FONT_FAMILY, 9),
                    wraplength=396,
                    justify="left",
                ).pack(fill=tk.X, anchor="w")

                tk.Label(
                    self._content,
                    text=f"→ {translation}",
                    fg=TRANS_COLOR,
                    bg=BG_COLOR,
                    font=(FONT_FAMILY, 11, "bold"),
                    wraplength=396,
                    justify="left",
                ).pack(fill=tk.X, anchor="w", pady=(0, 2))

        self._snap_to_bottom_right()
        self.window.deiconify()
        self._schedule_fade()

    def _show_error_ui(self, message: str) -> None:
        self._cancel_loading()
        self._clear_content()

        tk.Label(
            self._content,
            text=f"エラー: {message}",
            fg=ERROR_COLOR,
            bg=BG_COLOR,
            font=(FONT_FAMILY, 10),
            wraplength=396,
            justify="left",
        ).pack(anchor="w")

        self._snap_to_bottom_right()
        self.window.deiconify()
        self._schedule_fade()

    def _clear_content(self) -> None:
        for w in self._content.winfo_children():
            w.destroy()

    # ------------------------------------------------------------------ #
    # フェードアウト
    # ------------------------------------------------------------------ #

    def _schedule_fade(self) -> None:
        self._cancel_fade()
        ms = self.config.display_duration * 1000
        self._fade_id = self.root.after(ms, lambda: self._do_fade(self.config.opacity))

    def _do_fade(self, alpha: float) -> None:
        if alpha <= 0.0:
            self.window.withdraw()
            self.window.wm_attributes("-alpha", self.config.opacity)
            return
        self.window.wm_attributes("-alpha", alpha)
        self._fade_id = self.root.after(40, lambda: self._do_fade(round(alpha - 0.06, 2)))

    def _cancel_fade(self) -> None:
        if self._fade_id:
            self.root.after_cancel(self._fade_id)
            self._fade_id = None
        self.window.wm_attributes("-alpha", self.config.opacity)

    def _cancel_loading(self) -> None:
        if self._loading_id:
            self.root.after_cancel(self._loading_id)
            self._loading_id = None
        # 参照をクリア（実際の Widget 破棄は _clear_content に任せる）
        self._loading_label = None
