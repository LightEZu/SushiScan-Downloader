#!/usr/bin/env python3
"""
SushiScan Downloader v4
Dépendances : pip install selenium webdriver-manager requests beautifulsoup4 Pillow
"""

import subprocess, sys

def _auto_install():
    import importlib.util
    if getattr(sys, "frozen", False):
        return
    pkgs = {"selenium":"selenium","webdriver_manager":"webdriver-manager",
            "requests":"requests","bs4":"beautifulsoup4","PIL":"Pillow"}
    missing = [p for imp,p in pkgs.items() if not importlib.util.find_spec(imp)]
    if missing:
        print(f"Installation des dépendances manquantes : {missing}")
        subprocess.check_call([sys.executable,"-m","pip","install","--quiet"]+missing)
        print("Installation terminée. Relance le script.")
        sys.exit(0)

try:
    _auto_install()
except Exception as e:
    print(f"Erreur auto-install (non bloquant) : {e}")

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading, os, re, time, zipfile, traceback
from pathlib import Path

# ─── Themes ───────────────────────────────────────────────────────────────────

THEMES = {
    "Midnight": {
        "bg":"#0f1117","sidebar":"#13151c","card":"#1a1d27","border":"#2a2d3e",
        "accent":"#7c5cfc","accent2":"#a78bfa","text":"#e2e8f0","muted":"#4a5568",
        "entry_bg":"#0d0f18","ok":"#4ade80","warn":"#fbbf24","err":"#f87171",
        "step":"#818cf8","prog":"#7c5cfc","icon":"🌙",
    },
    "Café": {
        "bg":"#1a120b","sidebar":"#201610","card":"#2a1e14","border":"#3a2a1c",
        "accent":"#d4a853","accent2":"#f0c97a","text":"#f0e6d3","muted":"#7a6050",
        "entry_bg":"#140e08","ok":"#86efac","warn":"#fcd34d","err":"#f87171",
        "step":"#d4a853","prog":"#d4a853","icon":"☕",
    },
    "Cyberpunk": {
        "bg":"#08080f","sidebar":"#0a0a14","card":"#0f0f1c","border":"#1a1a30",
        "accent":"#ff2d78","accent2":"#00f0ff","text":"#e0e0ff","muted":"#4a4a7a",
        "entry_bg":"#060609","ok":"#00f0a0","warn":"#ffcc00","err":"#ff2d78",
        "step":"#00f0ff","prog":"#ff2d78","icon":"⚡",
    },
    "Synthwave": {
        "bg":"#100828","sidebar":"#140a30","card":"#1a1040","border":"#281860",
        "accent":"#f72585","accent2":"#b5179e","text":"#f0d8ff","muted":"#6a4f90",
        "entry_bg":"#0c061e","ok":"#4cc9f0","warn":"#f4a261","err":"#f72585",
        "step":"#9b5de5","prog":"#f72585","icon":"🎵",
    },
    "Nord": {
        "bg":"#2e3440","sidebar":"#272c38","card":"#3b4252","border":"#434c5e",
        "accent":"#88c0d0","accent2":"#81a1c1","text":"#eceff4","muted":"#6a7888",
        "entry_bg":"#252a35","ok":"#a3be8c","warn":"#ebcb8b","err":"#bf616a",
        "step":"#88c0d0","prog":"#88c0d0","icon":"❄️",
    },
    "Rose Gold": {
        "bg":"#180f16","sidebar":"#1e1220","card":"#261728","border":"#38203a",
        "accent":"#e8a0b0","accent2":"#f4c2cc","text":"#fce4ec","muted":"#7a5068",
        "entry_bg":"#120c12","ok":"#a5d6a7","warn":"#ffe082","err":"#ef9a9a",
        "step":"#e8a0b0","prog":"#e8a0b0","icon":"🌸",
    },
    "Dracula": {
        "bg":"#282a36","sidebar":"#21222c","card":"#323445","border":"#44475a",
        "accent":"#bd93f9","accent2":"#ff79c6","text":"#f8f8f2","muted":"#5a6280",
        "entry_bg":"#1c1e2a","ok":"#50fa7b","warn":"#ffb86c","err":"#ff5555",
        "step":"#8be9fd","prog":"#bd93f9","icon":"🧛",
    },
    "Ochin": {
        "bg":"#0b1d2c","sidebar":"#091828","card":"#102232","border":"#183042",
        "accent":"#38bdf8","accent2":"#7dd3fc","text":"#e0f2fe","muted":"#3a6a86",
        "entry_bg":"#07111c","ok":"#86efac","warn":"#fde68a","err":"#fca5a5",
        "step":"#38bdf8","prog":"#38bdf8","icon":"🌊",
    },
}

# ─── Rounded canvas helpers ───────────────────────────────────────────────────

def rounded_rect(canvas, x1, y1, x2, y2, r=10, **kwargs):
    """Draw a rounded rectangle on a Canvas."""
    points = [
        x1+r, y1,  x2-r, y1,
        x2, y1,    x2, y1+r,
        x2, y2-r,  x2, y2,
        x2-r, y2,  x1+r, y2,
        x1, y2,    x1, y2-r,
        x1, y1+r,  x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


class RoundedFrame(tk.Canvas):
    """A frame with rounded corners drawn via Canvas."""
    def __init__(self, parent, bg_outer, bg_inner, radius=12, border_color=None,
                 border_width=1, **kwargs):
        super().__init__(parent, bg=bg_outer, highlightthickness=0, **kwargs)
        self._bg_inner = bg_inner
        self._radius = radius
        self._border_color = border_color
        self._border_width = border_width
        self.bind("<Configure>", self._redraw)
        # Interior frame to place widgets
        self.inner = tk.Frame(self, bg=bg_inner)

    def _redraw(self, event=None):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        r = self._radius
        if self._border_color:
            rounded_rect(self, 0, 0, w, h, r, fill=self._border_color, outline="")
            bw = self._border_width
            rounded_rect(self, bw, bw, w-bw, h-bw, max(r-bw,1),
                         fill=self._bg_inner, outline="")
        else:
            rounded_rect(self, 0, 0, w, h, r, fill=self._bg_inner, outline="")
        # Keep inner frame on top
        self.inner.lift()

    def place_inner(self, pad=12):
        self.inner.place(x=pad, y=pad, relwidth=1.0, relheight=1.0,
                         width=-pad*2, height=-pad*2)


class RoundedButton(tk.Canvas):
    """A button with rounded corners."""
    def __init__(self, parent, text, command, bg, fg, bg_hover=None,
                 font=None, radius=8, padx=16, pady=8, state="normal", **kwargs):
        self._text = text
        self._command = command
        self._bg = bg
        self._fg = fg
        self._bg_hover = bg_hover or bg
        self._radius = radius
        self._padx = padx
        self._pady = pady
        self._font = font or ("Segoe UI", 10)
        self._state = state
        self._hovered = False

        # Measure text size
        tmp = tk.Label(parent, text=text, font=self._font)
        tmp.update_idletasks()
        w = tmp.winfo_reqwidth() + padx * 2
        h = tmp.winfo_reqheight() + pady * 2
        tmp.destroy()

        super().__init__(parent, width=w, height=h, bg=parent.cget("bg"),
                         highlightthickness=0, cursor="hand2" if state=="normal" else "", **kwargs)
        self._draw()
        # Always bind — _on_click and _on_enter check state internally
        self.bind("<Enter>",    self._on_enter)
        self.bind("<Leave>",    self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _draw(self):
        self.delete("all")
        w, h = int(self["width"]), int(self["height"])
        if self._state == "disabled":
            col = "#333344"
            fg  = "#555566"
        else:
            col = self._bg_hover if self._hovered else self._bg
            fg  = self._fg
        rounded_rect(self, 0, 0, w, h, self._radius, fill=col, outline="")
        self.create_text(w//2, h//2, text=self._text, fill=fg,
                         font=self._font, anchor="center")

    def _on_enter(self, e):
        if self._state == "normal":
            self._hovered = True
            self._draw()

    def _on_leave(self, e):
        if self._state == "normal":
            self._hovered = False
            self._draw()

    def _on_click(self, e):
        if self._state == "normal" and self._command:
            self._command()

    def config_state(self, state):
        self._state = state
        self._hovered = False
        self.configure(cursor="hand2" if state=="normal" else "")
        self._draw()


# ─── App ──────────────────────────────────────────────────────────────────────

class SushiScanDownloader:

    def __init__(self, root):
        self.root = root
        self.root.title("SushiScan Downloader")
        self.root.geometry("1020x700")
        self.root.minsize(860, 600)
        self.root.resizable(True, True)

        self.driver = None
        self.running = False
        self.continue_event = threading.Event()
        self.current_theme = "Midnight"
        self.theme = THEMES["Midnight"]

        # Persistent vars
        self.url_start_var = tk.StringVar()
        self.url_end_var   = tk.StringVar()
        self.cbz_name_var  = tk.StringVar()
        self.folder_var    = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.pause_var     = tk.IntVar(value=30)
        self.headless_var  = tk.BooleanVar(value=False)
        self.split_cbz_var  = tk.BooleanVar(value=False)
        self._cbz_name_event  = threading.Event()
        self._cbz_name_result = None
        self.status_var    = tk.StringVar(value="En attente…")

        self._build_ui()

    # ── Theme ────────────────────────────────────────────────────────────────

    def _apply_ttk(self):
        t = self.theme
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("TProgressbar", troughcolor=t["entry_bg"],
                    background=t["accent"], borderwidth=0, thickness=3)
        s.configure("TSpinbox", fieldbackground=t["entry_bg"], foreground=t["text"],
                    insertcolor=t["accent"], arrowcolor=t["muted"],
                    bordercolor=t["border"], font=("Segoe UI", 10))

    def _switch_theme(self, name):
        self.current_theme = name
        self.theme = THEMES[name]
        for w in self.root.winfo_children():
            w.destroy()
        self._build_ui()

    # ── UI ───────────────────────────────────────────────────────────────────

    def _build_ui(self):
        t = self.theme
        self._apply_ttk()
        self.root.configure(bg=t["bg"])

        outer = tk.Frame(self.root, bg=t["bg"])
        outer.pack(fill=tk.BOTH, expand=True)

        # ════ SIDEBAR ════
        sidebar = tk.Frame(outer, bg=t["sidebar"], width=190)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        # Subtle right border on sidebar
        tk.Frame(outer, bg=t["border"], width=1).pack(side=tk.LEFT, fill=tk.Y)

        # Logo
        logo_frame = tk.Frame(sidebar, bg=t["sidebar"])
        logo_frame.pack(fill=tk.X, padx=16, pady=(22, 2))
        tk.Label(logo_frame, text="🍣", bg=t["sidebar"], fg=t["accent"],
                 font=("Segoe UI", 18)).pack(side=tk.LEFT)
        tk.Label(logo_frame, text="SushiScan", bg=t["sidebar"], fg=t["text"],
                 font=("Segoe UI", 13, "bold")).pack(side=tk.LEFT, padx=(8,0))

        tk.Label(sidebar, text="Downloader  v4", bg=t["sidebar"], fg=t["muted"],
                 font=("Segoe UI", 8)).pack(anchor="w", padx=20, pady=(0,20))

        # Divider
        tk.Frame(sidebar, bg=t["border"], height=1).pack(fill=tk.X, padx=16, pady=(0,16))

        tk.Label(sidebar, text="THÈMES", bg=t["sidebar"], fg=t["muted"],
                 font=("Segoe UI", 7, "bold")).pack(anchor="w", padx=20, pady=(0,8))

        for name, data in THEMES.items():
            active = (name == self.current_theme)
            row = tk.Frame(sidebar, bg=t["sidebar"])
            row.pack(fill=tk.X, padx=10, pady=1)

            if active:
                # Pill indicator
                pill = tk.Frame(row, bg=t["accent"], width=3)
                pill.pack(side=tk.LEFT, fill=tk.Y, padx=(0,0))

            btn = tk.Button(
                row,
                text=f"  {data['icon']}  {name}",
                anchor="w",
                bg=t["card"] if active else t["sidebar"],
                fg=t["text"] if active else t["muted"],
                activebackground=t["card"],
                activeforeground=t["text"],
                font=("Segoe UI", 9, "bold" if active else "normal"),
                relief="flat", borderwidth=0, cursor="hand2",
                padx=10, pady=6,
                command=lambda n=name: self._switch_theme(n),
            )
            btn.pack(fill=tk.X)

        tk.Label(sidebar, text="sushiscan.net\nUsage personnel uniquement",
                 bg=t["sidebar"], fg=t["muted"], font=("Segoe UI", 7),
                 justify="left").pack(side=tk.BOTTOM, anchor="w", padx=20, pady=16)

        # ════ MAIN ════
        main = tk.Frame(outer, bg=t["bg"])
        main.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollable content
        canvas_scroll = tk.Canvas(main, bg=t["bg"], highlightthickness=0)
        canvas_scroll.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(main, orient="vertical", command=canvas_scroll.yview)
        # Don't show scrollbar unless needed — connect silently
        canvas_scroll.configure(yscrollcommand=scrollbar.set)

        content = tk.Frame(canvas_scroll, bg=t["bg"])
        content_window = canvas_scroll.create_window((0,0), window=content, anchor="nw")

        def _on_frame_configure(e):
            canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all"))
            # Show scrollbar only if needed
            if content.winfo_reqheight() > canvas_scroll.winfo_height():
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y, before=canvas_scroll)
            else:
                scrollbar.pack_forget()

        def _on_canvas_configure(e):
            canvas_scroll.itemconfig(content_window, width=e.width)

        content.bind("<Configure>", _on_frame_configure)
        canvas_scroll.bind("<Configure>", _on_canvas_configure)
        canvas_scroll.bind("<MouseWheel>", lambda e: canvas_scroll.yview_scroll(-1*(e.delta//120),"units"))

        # ── Padding wrapper ──
        wrap = tk.Frame(content, bg=t["bg"])
        wrap.pack(fill=tk.BOTH, expand=True, padx=28, pady=24)

        # ── Page title ──
        title_row = tk.Frame(wrap, bg=t["bg"])
        title_row.pack(fill=tk.X, pady=(0,20))
        tk.Label(title_row, text="Téléchargement", bg=t["bg"], fg=t["text"],
                 font=("Segoe UI", 18, "bold")).pack(side=tk.LEFT)
        tk.Label(title_row, textvariable=self.status_var, bg=t["bg"], fg=t["muted"],
                 font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(16,0), pady=(8,0))

        # ── URLs card ──
        self._label(wrap, "URLs")
        c1 = self._card(wrap)
        self._field_row(c1, "URL début", self.url_start_var, 0,
                        "https://sushiscan.net/nom-du-manga-volume-1/")
        self._field_row(c1, "URL fin  (optionnel)", self.url_end_var, 1,
                        "Laisser vide pour un seul tome")
        tk.Label(c1, text="ex: …/the-boys-edition-deluxe-volume-1/  ·  …/one-piece-chapitre-1100/",
                 bg=t["card"], fg=t["muted"], font=("Segoe UI", 8)
                 ).grid(row=2, column=0, columnspan=2, sticky="w", padx=(0,0), pady=(0,4))

        # ── Output card ──
        self._label(wrap, "Sortie")
        c2 = self._card(wrap)
        self._field_row(c2, "Nom CBZ  (optionnel)", self.cbz_name_var, 0,
                        "the-boys-volume-1  (sans .cbz)")

        fr = tk.Frame(c2, bg=t["card"])
        fr.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8,2))
        tk.Label(fr, text="Dossier", bg=t["card"], fg=t["muted"],
                 font=("Segoe UI", 9), width=18, anchor="w").pack(side=tk.LEFT)
        self._entry(fr, self.folder_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8,8))
        tk.Button(fr, text="Parcourir",
                  bg=t["border"], fg=t["text"],
                  activebackground=t["muted"], activeforeground=t["bg"],
                  relief="flat", font=("Segoe UI", 9), cursor="hand2",
                  padx=12, pady=4, command=self._browse_folder
                  ).pack(side=tk.LEFT)

        # ── Options card ──
        self._label(wrap, "Options")
        c3 = self._card(wrap)
        opt_row = tk.Frame(c3, bg=t["card"])
        opt_row.pack(fill=tk.X)
        tk.Label(opt_row, text="Pause entre chapitres (s)", bg=t["card"], fg=t["muted"],
                 font=("Segoe UI", 9)).pack(side=tk.LEFT)
        ttk.Spinbox(opt_row, from_=5, to=300, textvariable=self.pause_var,
                    width=5).pack(side=tk.LEFT, padx=(8,28))
        tk.Checkbutton(opt_row, text="Mode headless  (décocher si Cloudflare bloque)",
                       variable=self.headless_var,
                       bg=t["card"], fg=t["muted"],
                       selectcolor=t["entry_bg"], activebackground=t["card"],
                       activeforeground=t["text"], font=("Segoe UI", 9),
                       borderwidth=0).pack(side=tk.LEFT)

        opt_row2 = tk.Frame(c3, bg=t["card"])
        opt_row2.pack(fill=tk.X, pady=(6,0))
        tk.Checkbutton(opt_row2,
                       text="Un .cbz par chapitre avec nom personnalisé",
                       variable=self.split_cbz_var,
                       bg=t["card"], fg=t["muted"],
                       selectcolor=t["entry_bg"], activebackground=t["card"],
                       activeforeground=t["text"], font=("Segoe UI", 9),
                       borderwidth=0).pack(side=tk.LEFT)

        # ── Action buttons ──
        btn_row = tk.Frame(wrap, bg=t["bg"])
        btn_row.pack(fill=tk.X, pady=(16,4))

        self.start_btn = RoundedButton(
            btn_row, "▶   Démarrer", self._start,
            bg=t["accent"], fg=t["bg"], bg_hover=t["accent2"],
            font=("Segoe UI", 10, "bold"), radius=8, padx=22, pady=10)
        self.start_btn.pack(side=tk.LEFT)

        self.stop_btn = RoundedButton(
            btn_row, "⏹   Arrêter", self._stop,
            bg=t["card"], fg=t["muted"], bg_hover=t["border"],
            font=("Segoe UI", 10), radius=8, padx=16, pady=10, state="disabled")
        self.stop_btn.pack(side=tk.LEFT, padx=(10,0))

        self.continue_btn = RoundedButton(
            btn_row, "✓   Continuer", self._continue,
            bg="#166534", fg="#dcfce7", bg_hover="#15803d",
            font=("Segoe UI", 10, "bold"), radius=8, padx=22, pady=10, state="disabled")
        self.continue_btn.pack(side=tk.LEFT, padx=(10,0))

        # ── Progress ──
        prog_wrap = tk.Frame(wrap, bg=t["bg"])
        prog_wrap.pack(fill=tk.X, pady=(12,0))
        self.progress = ttk.Progressbar(prog_wrap, mode="determinate")
        self.progress.pack(fill=tk.X)

        # ── Log ──
        self._label(wrap, "Journal")
        self.log = scrolledtext.ScrolledText(
            wrap, bg=t["entry_bg"], fg=t["muted"],
            font=("Consolas", 9), relief="flat",
            wrap=tk.WORD, state=tk.DISABLED, height=9,
            insertbackground=t["accent"], selectbackground=t["border"],
            borderwidth=0)
        self.log.pack(fill=tk.BOTH, expand=True, pady=(0,8))
        self.log.tag_config("info", foreground=t["muted"])
        self.log.tag_config("ok",   foreground=t["ok"])
        self.log.tag_config("warn", foreground=t["warn"])
        self.log.tag_config("err",  foreground=t["err"])
        self.log.tag_config("step", foreground=t["step"])

    # ── UI helpers ───────────────────────────────────────────────────────────

    def _label(self, parent, text):
        """Small section label above a card."""
        t = self.theme
        tk.Label(parent, text=text.upper(), bg=t["bg"], fg=t["muted"],
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(14,4))

    def _card(self, parent):
        """Rounded card — returns inner grid frame."""
        t = self.theme
        # Outer frame with border color
        outer = tk.Frame(parent, bg=t["border"], padx=1, pady=1)
        outer.pack(fill=tk.X, pady=(0,2))
        # Inner
        inner = tk.Frame(outer, bg=t["card"])
        inner.pack(fill=tk.BOTH, expand=True)
        grid = tk.Frame(inner, bg=t["card"])
        grid.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)
        grid.columnconfigure(1, weight=1)
        return grid

    def _entry(self, parent, var, placeholder=None):
        """Styled entry widget."""
        t = self.theme
        current = var.get() if var else ""
        fg = t["muted"] if (not current or current == placeholder) else t["text"]
        e = tk.Entry(parent, textvariable=var,
                     bg=t["entry_bg"], fg=fg,
                     insertbackground=t["accent"],
                     relief="flat", font=("Segoe UI", 10),
                     bd=0, highlightthickness=1,
                     highlightbackground=t["border"],
                     highlightcolor=t["accent"])
        if placeholder and not current:
            var.set(placeholder)
            e.config(fg=t["muted"])
        return e

    def _field_row(self, grid, label, var, row, placeholder=""):
        """Label + entry in a grid row."""
        t = self.theme
        tk.Label(grid, text=label, bg=t["card"], fg=t["muted"],
                 font=("Segoe UI", 9), width=20, anchor="w"
                 ).grid(row=row, column=0, sticky="w", pady=6)

        current = var.get()
        fg = t["muted"] if (not current or current == placeholder) else t["text"]
        if not current:
            var.set(placeholder)

        entry = tk.Entry(grid, textvariable=var,
                         bg=t["entry_bg"], fg=fg,
                         insertbackground=t["accent"],
                         relief="flat", font=("Segoe UI", 10),
                         bd=0, highlightthickness=1,
                         highlightbackground=t["border"],
                         highlightcolor=t["accent"])
        entry.grid(row=row, column=1, sticky="ew", padx=(10,0), pady=6)

        def on_in(e, v=var, en=entry, ph=placeholder):
            if v.get() == ph:
                v.set("")
                en.config(fg=t["text"])
        def on_out(e, v=var, en=entry, ph=placeholder):
            if not v.get().strip():
                v.set(ph)
                en.config(fg=t["muted"])

        entry.bind("<FocusIn>",  on_in)
        entry.bind("<FocusOut>", on_out)

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _log(self, msg, tag="info"):
        def _do():
            self.log.config(state=tk.NORMAL)
            self.log.insert(tk.END, msg + "\n", tag)
            self.log.see(tk.END)
            self.log.config(state=tk.DISABLED)
        self.root.after(0, _do)

    def _set_status(self, msg):
        self.root.after(0, lambda: self.status_var.set(msg))

    def _set_progress(self, val):
        self.root.after(0, lambda: self.progress.configure(value=val))

    def _browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.folder_var.get())
        if folder:
            self.folder_var.set(folder)

    def _get_field(self, var, placeholder):
        val = var.get().strip()
        if val.startswith("http"):
            return val
        return "" if val == placeholder else val

    # ── Controls ────────────────────────────────────────────────────────────

    def _start(self):
        url = self._get_field(self.url_start_var, "https://sushiscan.net/nom-du-manga-volume-1/")
        if not url.startswith("http"):
            messagebox.showerror("Erreur", "Entre une URL valide (commence par https://).")
            return
        self.running = True
        self.start_btn.config_state("disabled")
        self.stop_btn.config_state("normal")
        self.continue_btn.config_state("disabled")
        self.continue_event.clear()
        self._log(f"🚀 Démarrage : {url}", "step")
        threading.Thread(target=self._run, daemon=True).start()

    def _stop(self):
        self.running = False
        self.continue_event.set()
        self._log("⏹ Arrêt demandé.", "warn")
        self._reset_buttons()

    def _continue(self):
        self.continue_event.set()
        self.root.after(0, lambda: self.continue_btn.config_state("disabled"))

    def _reset_buttons(self):
        def _do():
            self.start_btn.config_state("normal")
            self.stop_btn.config_state("disabled")
            self.continue_btn.config_state("disabled")
        self.root.after(0, _do)

    def _wait_continue(self, msg):
        self._log(f"⏳ {msg}", "warn")
        self._set_status(msg)
        self.root.after(0, lambda: self.continue_btn.config_state("normal"))
        self.continue_event.wait()
        self.continue_event.clear()

    # ── Core ────────────────────────────────────────────────────────────────

    def _run(self):
        try:
            self._run_inner()
        except Exception as e:
            self._log(f"❌ Erreur inattendue : {e}", "err")
            self._log(traceback.format_exc(), "err")
            self._reset_buttons()

    def _run_inner(self):
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager

        PH_START = "https://sushiscan.net/nom-du-manga-volume-1/"
        PH_END   = "Laisser vide pour un seul tome"
        PH_CBZ   = "the-boys-volume-1  (sans .cbz)"

        url_start = self._get_field(self.url_start_var, PH_START)
        url_end   = self._get_field(self.url_end_var,   PH_END)
        cbz_name  = self._get_field(self.cbz_name_var,  PH_CBZ)
        out_dir   = self.folder_var.get()
        pause     = self.pause_var.get()
        headless   = self.headless_var.get()
        split_cbz  = self.split_cbz_var.get()

        os.makedirs(out_dir, exist_ok=True)

        entries = self._build_list(url_start, url_end)
        if not entries:
            self._log("❌ Liste vide.", "err")
            self._reset_buttons()
            return
        self._log(f"📚 {len(entries)} entrée(s) à télécharger.", "step")

        opts = Options()
        if headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--window-size=1280,900")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=opts)
            self.driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"},
            )
        except Exception as e:
            self._log(f"❌ Impossible de lancer Chrome : {e}", "err")
            self._reset_buttons()
            return

        all_images = {}
        created_cbz = []

        try:
            for idx, (chap_url, slug) in enumerate(entries):
                if not self.running:
                    break
                self._log(f"\n{'─'*50}", "info")
                self._log(f"📖 [{idx+1}/{len(entries)}] {slug}", "step")
                self._set_progress(int(idx / len(entries) * 100))
                imgs = self._download_entry(chap_url, slug, out_dir,
                                            pause if idx > 0 else 0)
                if not imgs:
                    self._log(f"⚠️  Aucune image pour {slug}.", "warn")
                    continue

                self._log(f"✅ {len(imgs)} pages.", "ok")

                if split_cbz:
                    # Ask user for CBZ name right after each chapter
                    name = self._ask_cbz_name(slug, idx + 1, len(entries))
                    if name is None:  # user cancelled / stopped
                        break
                    self._set_status("Création du CBZ…")
                    path = self._make_cbz({slug: imgs}, name, out_dir, [(chap_url, slug)])
                    if path:
                        self._log(f"📦 {os.path.basename(path)}", "ok")
                        created_cbz.append(path)
                else:
                    all_images[slug] = imgs

        finally:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None

        if not self.running:
            self._log("⏹ Interrompu.", "warn")
            self._reset_buttons()
            return

        if split_cbz:
            if created_cbz:
                self._log(f"\n🎉 {len(created_cbz)} fichier(s) CBZ créés dans :\n{out_dir}", "ok")
                messagebox.showinfo("Terminé !",
                    f"{len(created_cbz)} fichier(s) CBZ créés dans :\n{out_dir}")
            else:
                self._log("❌ Aucun CBZ créé.", "err")
        elif all_images:
            self._set_status("Création du CBZ…")
            path = self._make_cbz(all_images, cbz_name, out_dir, entries)
            if path:
                self._log(f"\n🎉 CBZ créé : {path}", "ok")
                messagebox.showinfo("Terminé !", f"Fichier CBZ :\n{path}")
        else:
            self._log("❌ Aucune image à compresser.", "err")

        self._set_progress(100)
        self._set_status("Terminé.")
        self._reset_buttons()

    # ── Build URL list ───────────────────────────────────────────────────────

    def _build_list(self, url_start, url_end):
        def slug(u):
            return u.rstrip("/").split("/")[-1]
        if not url_end:
            return [(url_start, slug(url_start))]

        def extract(url):
            last = url.rstrip("/").split("/")[-1]
            m = re.search(r"(\d+(?:[.,]\d+)?)(?:[^0-9]*)$", last)
            if not m:
                return None, None
            num = m.group(1)
            i = url.rfind(num)
            return float(num.replace(",",".")), url[:i] + "{N}" + url[i+len(num):]

        s_num, tmpl = extract(url_start)
        e_num, _    = extract(url_end)
        if s_num is None or e_num is None:
            self._log("⚠️  Plage non détectée — téléchargement du seul chapitre de début.", "warn")
            return [(url_start, slug(url_start))]

        entries, n = [], s_num
        while n <= e_num + 0.001:
            ns = str(int(n)) if n == int(n) else str(round(n,1))
            u = tmpl.replace("{N}", ns)
            entries.append((u, slug(u)))
            n += 1
            if n > s_num + 1000:
                break
        return entries

    # ── Download one entry ───────────────────────────────────────────────────

    def _download_entry(self, url, slug, out_dir, pre_pause):
        if pre_pause > 0:
            self._log(f"💤 Pause {pre_pause}s…", "info")
            for _ in range(pre_pause):
                if not self.running:
                    return []
                time.sleep(1)

        self._log(f"🌐 Ouverture : {url}", "info")
        try:
            self.driver.get(url)
        except Exception as e:
            self._log(f"❌ Navigation échouée : {e}", "err")
            return []

        time.sleep(3)
        self._wait_continue("Étape 1/2 — Résous le captcha si nécessaire, puis clique Continuer.")
        if not self.running:
            return []

        self._try_vertical_mode()
        time.sleep(2)

        self._wait_continue("Étape 2/2 — Attends que toutes les images soient visibles, puis clique Continuer.")
        if not self.running:
            return []

        img_urls = self._extract_images()
        if not img_urls:
            self._log("⚠️  Aucune image détectée.", "warn")
            return []
        self._log(f"🖼  {len(img_urls)} images trouvées.", "info")

        chap_dir = os.path.join(out_dir, "_sushi_tmp", slug)
        os.makedirs(chap_dir, exist_ok=True)

        import requests
        session = requests.Session()
        try:
            for cookie in self.driver.get_cookies():
                session.cookies.set(cookie["name"], cookie["value"],
                                    domain=cookie.get("domain","").lstrip("."))
            self._log(f"🍪 {len(self.driver.get_cookies())} cookie(s) injectés.", "info")
        except Exception as e:
            self._log(f"⚠️  Cookies : {e}", "warn")

        try:
            ua = self.driver.execute_script("return navigator.userAgent;")
        except Exception:
            ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"

        domain = "/".join(url.rstrip("/").split("/")[:3])
        session.headers.update({
            "User-Agent": ua, "Referer": url, "Origin": domain,
            "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Sec-Fetch-Dest": "image", "Sec-Fetch-Mode": "no-cors",
            "Sec-Fetch-Site": "cross-site",
        })

        saved = []
        for i, img_url in enumerate(img_urls):
            if not self.running:
                break
            try:
                r = session.get(img_url, timeout=30)
                r.raise_for_status()
                ext = self._guess_ext(img_url, r.headers.get("Content-Type",""))
                fname = os.path.join(chap_dir, f"{i+1:03d}{ext}")
                with open(fname, "wb") as f:
                    f.write(r.content)
                saved.append(fname)
                self._set_status(f"{slug} — page {i+1}/{len(img_urls)}")
            except Exception as e:
                self._log(f"⚠️  Image {i+1} : {e}", "warn")
        return saved

    def _try_vertical_mode(self):
        xpaths = [
            "//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'lecture verticale')]",
            "//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'vertical')]",
        ]
        for xp in xpaths:
            try:
                self.driver.find_element("xpath", xp).click()
                time.sleep(1)
                self._log("↕️  Mode lecture verticale activé.", "info")
                return
            except Exception:
                continue

    def _extract_images(self):
        from selenium.webdriver.common.by import By
        imgs = []
        try:
            els = self.driver.find_elements(By.CSS_SELECTOR,
                "#readerarea img, .reading-content img, .read-container img, "
                "#chapter-images img, .entry-content img")
            for el in els:
                src = (el.get_attribute("src") or el.get_attribute("data-src") or
                       el.get_attribute("data-lazy") or "").strip()
                if src and self._is_page_image(src):
                    imgs.append(src)
        except Exception:
            pass
        if not imgs:
            try:
                for el in self.driver.find_elements(By.TAG_NAME, "img"):
                    src = (el.get_attribute("src") or el.get_attribute("data-src") or "").strip()
                    if src and self._is_page_image(src):
                        imgs.append(src)
            except Exception:
                pass
        if not imgs:
            try:
                found = re.findall(
                    r'https?://[^\s\'"<>\\]+\.(?:jpg|jpeg|png|webp)(?:\?[^\s\'"<>\\]*)?',
                    self.driver.page_source, re.IGNORECASE)
                imgs = [u for u in found if self._is_page_image(u)]
            except Exception:
                pass
        seen, result = set(), []
        for u in imgs:
            k = u.split("?")[0]
            if k not in seen:
                seen.add(k)
                result.append(u)
        return result

    def _is_page_image(self, url):
        u = url.lower()
        if not re.search(r"\.(jpg|jpeg|png|webp)(\?|$)", u):
            return False
        good = any(p in u for p in ("wp-content/uploads","sushiscan","/cdn/","manga","scan","page","chap","vol"))
        bad  = any(p in u for p in ("logo","icon","avatar","banner","favicon","thumbnail","placeholder","spinner","gravatar"))
        numeric = bool(re.search(r"/\d{2,4}\.(jpg|jpeg|png|webp)(\?|$)", u))
        return (good or numeric) and not bad

    def _guess_ext(self, url, ct):
        for k,v in {"image/jpeg":".jpg","image/jpg":".jpg","image/png":".png","image/webp":".webp"}.items():
            if k in ct:
                return v
        for ext in (".webp",".png",".jpg",".jpeg"):
            if ext in url.lower():
                return ".jpg" if ext == ".jpeg" else ext
        return ".jpg"

    # ── CBZ naming dialog ────────────────────────────────────────────────────

    def _ask_cbz_name(self, slug, current, total):
        """
        Opens a modal dialog on the UI thread asking the user to name the CBZ.
        Returns the chosen name string, or None if cancelled/stopped.
        Blocks the worker thread until the user confirms.
        """
        self._cbz_name_result = None
        self._cbz_name_event.clear()

        def _show_dialog():
            t = self.theme
            dlg = tk.Toplevel(self.root)
            dlg.title("Nommer le fichier CBZ")
            dlg.configure(bg=t["bg"])
            dlg.resizable(False, False)
            dlg.grab_set()  # modal

            # Center over main window
            self.root.update_idletasks()
            rx = self.root.winfo_x() + self.root.winfo_width()  // 2
            ry = self.root.winfo_y() + self.root.winfo_height() // 2
            dlg.geometry(f"460x210+{rx-230}+{ry-105}")

            # Header
            tk.Label(dlg,
                     text=f"Chapitre {current}/{total} téléchargé ✅",
                     bg=t["bg"], fg=t["ok"],
                     font=("Segoe UI", 11, "bold")).pack(pady=(20, 4))
            tk.Label(dlg,
                     text=f"Slug : {slug}",
                     bg=t["bg"], fg=t["muted"],
                     font=("Segoe UI", 8)).pack()

            tk.Label(dlg,
                     text="Nom du fichier .cbz  (sans extension) :",
                     bg=t["bg"], fg=t["text"],
                     font=("Segoe UI", 9)).pack(pady=(14, 4))

            # Entry pre-filled with slug
            name_var = tk.StringVar(value=slug)
            entry = tk.Entry(dlg, textvariable=name_var,
                             bg=t["entry_bg"], fg=t["text"],
                             insertbackground=t["accent"],
                             relief="flat", font=("Segoe UI", 11),
                             bd=0, highlightthickness=1,
                             highlightbackground=t["border"],
                             highlightcolor=t["accent"],
                             width=42)
            entry.pack(ipady=6, padx=24)
            entry.select_range(0, tk.END)
            entry.focus_set()

            # Buttons
            btn_row = tk.Frame(dlg, bg=t["bg"])
            btn_row.pack(pady=(16, 0))

            def confirm():
                val = name_var.get().strip()
                # Remove .cbz if user typed it
                if val.lower().endswith(".cbz"):
                    val = val[:-4].strip()
                self._cbz_name_result = val if val else slug
                dlg.destroy()
                self._cbz_name_event.set()

            def cancel():
                self._cbz_name_result = None
                self.running = False
                dlg.destroy()
                self._cbz_name_event.set()

            entry.bind("<Return>", lambda e: confirm())
            entry.bind("<Escape>", lambda e: cancel())

            tk.Button(btn_row, text="✓  Confirmer",
                      bg=t["accent"], fg=t["bg"],
                      activebackground=t["accent2"], activeforeground=t["bg"],
                      font=("Segoe UI", 10, "bold"), relief="flat",
                      cursor="hand2", padx=18, pady=7,
                      command=confirm).pack(side=tk.LEFT)

            tk.Button(btn_row, text="⏹  Arrêter",
                      bg=t["card"], fg=t["muted"],
                      activebackground=t["border"], activeforeground=t["text"],
                      font=("Segoe UI", 10), relief="flat",
                      cursor="hand2", padx=14, pady=7,
                      command=cancel).pack(side=tk.LEFT, padx=(10, 0))

            dlg.protocol("WM_DELETE_WINDOW", cancel)

        self.root.after(0, _show_dialog)
        self._cbz_name_event.wait()
        return self._cbz_name_result

    # ── CBZ ─────────────────────────────────────────────────────────────────

    def _make_cbz(self, all_images, cbz_name, out_dir, entries):
        if not cbz_name:
            slugs = [s for _,s in entries]
            if len(slugs) == 1:
                cbz_name = slugs[0]
            else:
                base = re.sub(r"[-_]?\d+$","",slugs[0]).rstrip("-_ ")
                m0 = re.search(r"\d+", slugs[0])
                m1 = re.search(r"\d+", slugs[-1])
                cbz_name = f"{base}-{m0.group()}-{m1.group()}" if m0 and m1 else f"{base}-multi"

        cbz_path = os.path.join(out_dir, cbz_name + ".cbz")
        try:
            with zipfile.ZipFile(cbz_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for slug, paths in all_images.items():
                    for p in sorted(paths):
                        zf.write(p, os.path.join(slug, os.path.basename(p)))
            import shutil
            tmp = os.path.join(out_dir, "_sushi_tmp")
            if os.path.exists(tmp):
                shutil.rmtree(tmp, ignore_errors=True)
            return cbz_path
        except Exception as e:
            self._log(f"❌ Erreur CBZ : {e}", "err")
            return None


# ─── Entry point ──────────────────────────────────────────────────────────────

def _set_window_icon(root):
    """Set window icon — works both as .py and compiled .exe (PyInstaller)."""
    import sys, os, tempfile
    ico_path = None

    # PyInstaller bundles files in sys._MEIPASS
    if hasattr(sys, "_MEIPASS"):
        candidate = os.path.join(sys._MEIPASS, "sushi.ico")
        if os.path.exists(candidate):
            ico_path = candidate
    
    # Running as plain .py — look next to the script
    if ico_path is None:
        candidate = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sushi.ico")
        if os.path.exists(candidate):
            ico_path = candidate

    if ico_path:
        try:
            root.iconbitmap(ico_path)
            return
        except Exception:
            pass

    # Fallback: embed a minimal 1x1 ICO so at least no crash
    try:
        root.iconbitmap(default="")
    except Exception:
        pass


def main():
    root = tk.Tk()
    _set_window_icon(root)
    app = SushiScanDownloader(root)

    def on_close():
        if app.running:
            if not messagebox.askyesno("Quitter", "Un téléchargement est en cours. Quitter ?"):
                return
        app.running = False
        app.continue_event.set()
        try:
            if app.driver:
                app.driver.quit()
        except Exception:
            pass
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

if __name__ == "__main__":
    main()
