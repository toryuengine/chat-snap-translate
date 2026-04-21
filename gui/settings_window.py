"""設定ウィンドウ"""
import tkinter as tk
from tkinter import messagebox, ttk


class SettingsWindow:
    def __init__(self, root: tk.Tk, config, hotkey_manager=None) -> None:
        self.root = root
        self.config = config
        self.hotkey_manager = hotkey_manager

        self.window = tk.Toplevel(root)
        self.window.title("設定")
        self.window.geometry("480x360")
        self.window.resizable(False, False)
        self.window.grab_set()
        self.window.focus_set()

        self._build()

    def _build(self) -> None:
        frame = ttk.Frame(self.window, padding=24)
        frame.pack(fill=tk.BOTH, expand=True)
        frame.columnconfigure(1, weight=1)

        row = 0

        # --- API 情報（.env から読み取り・編集不可） ---
        ttk.Label(frame, text="API 設定 (.env)",
                  font=("Segoe UI", 9, "bold"), foreground="#555555").grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(0, 4))
        row += 1

        api_info = (f"プロバイダー : {self.config.api_provider.upper()}\n"
                    f"モデル       : {self.config.active_model}\n"
                    f"API キー     : {'設定済み' if self.config.active_api_key else '未設定 ⚠'}")
        ttk.Label(frame, text=api_info, font=("Consolas", 9),
                  foreground="#1a6bc5", justify="left").grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(0, 12))
        row += 1

        ttk.Separator(frame, orient="horizontal").grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        row += 1

        # --- 変更可能な設定 ---
        ttk.Label(frame, text="アプリ設定",
                  font=("Segoe UI", 9, "bold"), foreground="#555555").grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(0, 4))
        row += 1

        # ホットキー
        self._hotkey_var = tk.StringVar(value=self.config.hotkey)
        self._add_row(frame, row, "ホットキー:",
                      ttk.Entry(frame, textvariable=self._hotkey_var, width=30))
        row += 1

        # 表示時間
        self._duration_var = tk.IntVar(value=self.config.display_duration)
        self._add_row(frame, row, "表示時間 (秒):",
                      ttk.Spinbox(frame, from_=3, to=60,
                                  textvariable=self._duration_var, width=10))
        row += 1

        # 透明度
        self._opacity_var = tk.IntVar(value=round(self.config.opacity * 100))
        opacity_frame = ttk.Frame(frame)
        ttk.Scale(opacity_frame, from_=30, to=100, variable=self._opacity_var,
                  orient="horizontal", length=160).pack(side=tk.LEFT)
        ttk.Label(opacity_frame, textvariable=self._opacity_var, width=4).pack(side=tk.LEFT, padx=4)
        ttk.Label(opacity_frame, text="%").pack(side=tk.LEFT)
        self._add_row(frame, row, "透明度:", opacity_frame)
        row += 1

        # ボタン
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=(20, 0))
        ttk.Button(btn_frame, text="保存", command=self._save).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_frame, text="キャンセル", command=self.window.destroy).pack(side=tk.LEFT, padx=6)

    def _add_row(self, frame: ttk.Frame, row: int, label: str, widget: tk.Widget) -> None:
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=6)
        widget.grid(row=row, column=1, sticky="ew", padx=(12, 0), pady=6)

    def _save(self) -> None:
        new_hotkey = self._hotkey_var.get().strip()
        old_hotkey = self.config.hotkey

        self.config.set("hotkey", new_hotkey)
        self.config.set("display_duration", self._duration_var.get())
        self.config.set("opacity", self._opacity_var.get() / 100)
        self.config.save()

        if self.hotkey_manager and new_hotkey != old_hotkey:
            try:
                self.hotkey_manager.rebind(new_hotkey)
            except Exception as e:
                messagebox.showerror("エラー", f"ホットキーの設定に失敗しました:\n{e}",
                                     parent=self.window)
                return

        messagebox.showinfo("設定", "設定を保存しました。", parent=self.window)
        self.window.destroy()
