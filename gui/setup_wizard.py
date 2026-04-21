"""初回セットアップウィザード"""
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk


class SetupWizard:
    """
    初回起動時に表示されるセットアップダイアログ。

    ステップ A (.env 未設定時のみ): .env ファイルの作成ガイド
    ステップ B (capture_area 未設定時): キャプチャエリアのドラッグ選択

    どちらも満たしている場合はウィザードを表示しない。
    """

    def __init__(self, root: tk.Tk, config) -> None:
        self.root = root
        self.config = config

        self.window = tk.Toplevel(root)
        self.window.title("初回セットアップ")
        self.window.geometry("500x400")
        self.window.resizable(False, False)
        self.window.grab_set()
        self.window.focus_set()
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_chrome()
        self._start()

    # ------------------------------------------------------------------ #
    # 共通レイアウト
    # ------------------------------------------------------------------ #

    def _build_chrome(self) -> None:
        outer = ttk.Frame(self.window, padding=28)
        outer.pack(fill=tk.BOTH, expand=True)

        ttk.Label(outer, text="ゲームチャット翻訳ツール",
                  font=("Segoe UI", 16, "bold")).pack()
        ttk.Label(outer, text="初回セットアップ",
                  font=("Segoe UI", 11), foreground="#555555").pack(pady=(2, 16))

        self._content = ttk.Frame(outer)
        self._content.pack(fill=tk.BOTH, expand=True)

        self._next_btn = ttk.Button(outer, text="次へ", command=self._next)
        self._next_btn.pack(pady=(14, 0))

    def _clear(self) -> None:
        for w in self._content.winfo_children():
            w.destroy()

    # ------------------------------------------------------------------ #
    # ステップ振り分け
    # ------------------------------------------------------------------ #

    def _start(self) -> None:
        if not self.config.is_env_ready():
            self._go_env_guide()
        else:
            self._go_capture()

    # ------------------------------------------------------------------ #
    # ステップ A: .env セットアップガイド
    # ------------------------------------------------------------------ #

    def _go_env_guide(self) -> None:
        self._clear()
        self._step = "env"

        ttk.Label(self._content, text=".env ファイルの設定",
                  font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 8))

        from core.config import ENV_PATH, PROJECT_ROOT
        env_example = PROJECT_ROOT / ".env.example"
        env_path = ENV_PATH

        guide = (
            f"API キーが見つかりません。\n"
            f"プロジェクトフォルダに .env ファイルを作成してください。\n\n"
            f"  場所: {env_path.resolve()}\n\n"
            f".env.example をコピーして .env を作成し、\n"
            f"API_PROVIDER と対応する API キー・モデル名を入力してください。"
        )
        ttk.Label(self._content, text=guide, justify="left",
                  foreground="#333333").pack(anchor="w", pady=(0, 12))

        # .env.example の内容をプレビュー表示
        if env_example.exists():
            preview = tk.Text(self._content, height=8, width=56,
                              font=("Consolas", 9), state="normal",
                              bg="#f5f5f5", relief="solid", borderwidth=1)
            preview.insert("1.0", env_example.read_text(encoding="utf-8"))
            preview.config(state="disabled")
            preview.pack(fill=tk.X, pady=(0, 8))

        self._next_btn.config(text=".env を作成しました → 再確認")

    # ------------------------------------------------------------------ #
    # ステップ B: キャプチャエリア選択
    # ------------------------------------------------------------------ #

    def _go_capture(self) -> None:
        self._clear()
        self._step = "capture"

        ttk.Label(self._content, text="キャプチャエリアの設定",
                  font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 8))
        ttk.Label(
            self._content,
            text=("「エリアを選択」をクリックすると画面が暗くなります。\n"
                  "ゲームのチャット部分をドラッグで選択してください。"),
            justify="left",
            foreground="#444444",
        ).pack(anchor="w", pady=(0, 12))

        status_row = ttk.Frame(self._content)
        status_row.pack(anchor="w", pady=(0, 8))
        ttk.Label(status_row, text="選択状態:").pack(side=tk.LEFT)
        self._area_status_var = tk.StringVar()
        self._refresh_area_status()
        ttk.Label(status_row, textvariable=self._area_status_var,
                  foreground="green").pack(side=tk.LEFT, padx=6)

        ttk.Button(self._content, text="エリアを選択",
                   command=self._select_area).pack(pady=6)

        self._next_btn.config(text="完了")

    def _refresh_area_status(self) -> None:
        area = self.config.capture_area
        if area:
            self._area_status_var.set(f"設定済み  ({area['width']} × {area['height']} px)")
        else:
            self._area_status_var.set("未設定")

    def _select_area(self) -> None:
        from gui.capture_selector import CaptureSelector

        # grab を解放してからウィンドウを隠す（grab が残るとマウスイベントを奪い続ける）
        self.window.grab_release()
        self.window.withdraw()
        selector = CaptureSelector(self.root, self.config)
        self.root.wait_window(selector.window)
        self.window.deiconify()
        self.window.grab_set()  # 戻ったら grab を再取得
        self._refresh_area_status()

    # ------------------------------------------------------------------ #
    # ナビゲーション
    # ------------------------------------------------------------------ #

    def _next(self) -> None:
        if self._step == "env":
            # .env を再読み込みして再チェック
            from dotenv import load_dotenv
            from core.config import ENV_PATH
            load_dotenv(dotenv_path=ENV_PATH, override=True)

            if not self.config.is_env_ready():
                messagebox.showwarning(
                    "未設定",
                    ".env ファイルに API キーが見つかりません。\n"
                    "ファイルを作成して API キーを入力してください。",
                    parent=self.window,
                )
                return
            self._go_capture()

        elif self._step == "capture":
            if not self.config.capture_area:
                messagebox.showwarning(
                    "未設定", "キャプチャエリアを選択してください。", parent=self.window
                )
                return
            self.config.save()
            self.window.destroy()

    def _on_close(self) -> None:
        if messagebox.askyesno("確認", "セットアップをキャンセルしてアプリを終了しますか？",
                               parent=self.window):
            self.root.quit()
