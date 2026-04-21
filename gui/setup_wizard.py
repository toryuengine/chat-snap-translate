""".env 未設定時のセットアップガイド"""
import tkinter as tk
from tkinter import messagebox, ttk


class SetupWizard:
    """
    .env に API キーが設定されていない場合のみ表示するガイドダイアログ。
    キャプチャエリア選択は main.py で毎回行うため、ここでは扱わない。
    """

    def __init__(self, root: tk.Tk, config) -> None:
        self.root = root
        self.config = config

        self.window = tk.Toplevel(root)
        self.window.title("セットアップ — API キーの設定")
        self.window.geometry("500x360")
        self.window.resizable(False, False)
        self.window.grab_set()
        self.window.focus_set()
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build()

    def _build(self) -> None:
        outer = ttk.Frame(self.window, padding=28)
        outer.pack(fill=tk.BOTH, expand=True)

        ttk.Label(outer, text="ゲームチャット翻訳ツール",
                  font=("Segoe UI", 16, "bold")).pack()
        ttk.Label(outer, text=".env ファイルの設定",
                  font=("Segoe UI", 11), foreground="#555555").pack(pady=(2, 16))

        from core.config import ENV_PATH, PROJECT_ROOT
        env_example = PROJECT_ROOT / ".env.example"

        guide = (
            f"API キーが見つかりません。\n"
            f"プロジェクトフォルダに .env ファイルを作成してください。\n\n"
            f"  場所: {ENV_PATH.resolve()}\n\n"
            f".env.example をコピーして .env を作成し、\n"
            f"API_PROVIDER と対応する API キー・モデル名を入力してください。"
        )
        ttk.Label(outer, text=guide, justify="left",
                  foreground="#333333").pack(anchor="w", pady=(0, 10))

        if env_example.exists():
            preview = tk.Text(outer, height=7, width=56,
                              font=("Consolas", 9), bg="#f5f5f5",
                              relief="solid", borderwidth=1)
            preview.insert("1.0", env_example.read_text(encoding="utf-8"))
            preview.config(state="disabled")
            preview.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(outer, text=".env を作成しました → 再確認",
                   command=self._recheck).pack(pady=(4, 0))

    def _recheck(self) -> None:
        from dotenv import load_dotenv
        from core.config import ENV_PATH
        load_dotenv(dotenv_path=ENV_PATH, override=True)

        if not self.config.is_env_ready():
            messagebox.showwarning(
                "未設定",
                ".env ファイルに API キーが見つかりません。\n"
                "ファイルを保存してから再確認してください。",
                parent=self.window,
            )
            return

        self.window.destroy()

    def _on_close(self) -> None:
        if messagebox.askyesno("確認", "セットアップをキャンセルしてアプリを終了しますか？",
                               parent=self.window):
            self.root.quit()
