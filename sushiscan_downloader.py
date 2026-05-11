#!/usr/bin/env python3
"""
SushiScan Downloader v3
Dépendances : pip install selenium webdriver-manager requests beautifulsoup4 Pillow
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading, os, re, time, zipfile, requests, traceback
from pathlib import Path

# ─── Themes ───────────────────────────────────────────────────────────────────

THEMES = {
    "Midnight": {
        "bg":"#0f1117","sidebar":"#13151c","card":"#1a1d27","border":"#2a2d3e",
        "accent":"#7c5cfc","accent2":"#a78bfa","text":"#e2e8f0","muted":"#64748b",
        "entry_bg":"#0d0f18","ok":"#4ade80","warn":"#fbbf24","err":"#f87171",
        "step":"#818cf8","prog":"#7c5cfc","icon":"🌙",
    },
    "Café": {
        "bg":"#1c1410","sidebar":"#231a13","card":"#2c2018","border":"#3d2e20",
        "accent":"#d4a853","accent2":"#f0c97a","text":"#f0e6d3","muted":"#8a7060",
        "entry_bg":"#161009","ok":"#86efac","warn":"#fcd34d","err":"#f87171",
        "step":"#d4a853","prog":"#d4a853","icon":"☕",
    },
    "Cyberpunk": {
        "bg":"#0a0a12","sidebar":"#0d0d18","card":"#12121f","border":"#1e1e35",
        "accent":"#ff2d78","accent2":"#00f0ff","text":"#e0e0ff","muted":"#5a5a8a",
        "entry_bg":"#08080f","ok":"#00f0a0","warn":"#ffcc00","err":"#ff2d78",
        "step":"#00f0ff","prog":"#ff2d78","icon":"⚡",
    },
    "Synthwave": {
        "bg":"#120b2e","sidebar":"#160d35","card":"#1e1245","border":"#2d1a5e",
        "accent":"#f72585","accent2":"#b5179e","text":"#f8d8ff","muted":"#7b5fa0",
        "entry_bg":"#0d0820","ok":"#4cc9f0","warn":"#f4a261","err":"#f72585",
        "step":"#7209b7","prog":"#f72585","icon":"🎵",
    },
    "Nord": {
        "bg":"#2e3440","sidebar":"#272c38","card":"#3b4252","border":"#434c5e",
        "accent":"#88c0d0","accent2":"#81a1c1","text":"#eceff4","muted":"#7b88a1",
        "entry_bg":"#252a35","ok":"#a3be8c","warn":"#ebcb8b","err":"#bf616a",
        "step":"#88c0d0","prog":"#88c0d0","icon":"❄️",
    },
    "Rose Gold": {
        "bg":"#1a1118","sidebar":"#1f1420","card":"#271929","border":"#3a2038",
        "accent":"#e8a0b0","accent2":"#f4c2cc","text":"#fce4ec","muted":"#8a6070",
        "entry_bg":"#140d14","ok":"#a5d6a7","warn":"#ffe082","err":"#ef9a9a",
        "step":"#e8a0b0","prog":"#e8a0b0","icon":"🌸",
    },
    "Dracula": {
        "bg":"#282a36","sidebar":"#21222c","card":"#343746","border":"#44475a",
        "accent":"#bd93f9","accent2":"#ff79c6","text":"#f8f8f2","muted":"#6272a4",
        "entry_bg":"#1e1f29","ok":"#50fa7b","warn":"#ffb86c","err":"#ff5555",
        "step":"#8be9fd","prog":"#bd93f9","icon":"🧛",
    },
    "Ochin": {
        "bg":"#0d1f2d","sidebar":"#0a1a26","card":"#122535","border":"#1a3347",
        "accent":"#38bdf8","accent2":"#7dd3fc","text":"#e0f2fe","muted":"#4a7a96",
        "entry_bg":"#091520","ok":"#86efac","warn":"#fde68a","err":"#fca5a5",
        "step":"#38bdf8","prog":"#38bdf8","icon":"🌊",
    },
}

# ─── App ──────────────────────────────────────────────────────────────────────

class SushiScanDownloader:

    def __init__(self, root):
        self.root = root
        self.root.title("🍣 SushiScan Downloader")

# --- AJOUT POUR L'ICÔNE DE LA FENÊTRE ---
        icon_file = "sushi.ico"
        try:
            # Cette ligne permet de trouver l'icône même dans le .exe
            if hasattr(sys, '_MEIPASS'):
                path = os.path.join(sys._MEIPASS, icon_file)
            else:
                path = os.path.abspath(icon_file)
            
            if os.path.exists(path):
                self.root.iconbitmap(path)
        except Exception:
            pass # Si l'icône échoue, on laisse la plume par défaut plutôt que de crash
        # ----------------------------------------
        
        self.root.geometry("1020x700")
        self.root.minsize(860, 580)
        self.root.resizable(True, True)

        self.driver = None
        self.running = False
        self.continue_event = threading.Event()
        self.current_theme = "Midnight"
        self.theme = THEMES["Midnight"]

        # Persistent state — survive theme switches
        self.url_start_var = tk.StringVar()
        self.url_end_var   = tk.StringVar()
        self.cbz_name_var  = tk.StringVar()
        self.folder_var    = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.pause_var     = tk.IntVar(value=30)
        self.headless_var  = tk.BooleanVar(value=False)
        self.status_var    = tk.StringVar(value="En attente…")

        self._build_ui()

    # ── Theme ────────────────────────────────────────────────────────────────

    def _apply_ttk(self):
        t = self.theme
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("TProgressbar", troughcolor=t["entry_bg"], background=t["prog"],
                    borderwidth=0, thickness=4)
        s.configure("TSpinbox", fieldbackground=t["entry_bg"], foreground=t["text"],
                    insertcolor=t["accent"], arrowcolor=t["accent"],
                    bordercolor=t["border"], font=("Consolas", 10))

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
        sidebar = tk.Frame(outer, bg=t["sidebar"], width=185)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        # Logo
        logo = tk.Frame(sidebar, bg=t["sidebar"])
        logo.pack(fill=tk.X, padx=14, pady=(18, 4))
        tk.Label(logo, text="🍣", bg=t["sidebar"], fg=t["accent"],
                 font=("Consolas", 20)).pack(side=tk.LEFT)
        tk.Label(logo, text="SushiScan", bg=t["sidebar"], fg=t["text"],
                 font=("Consolas", 12, "bold")).pack(side=tk.LEFT, padx=(6,0))

        tk.Label(sidebar, text="Downloader v3", bg=t["sidebar"], fg=t["muted"],
                 font=("Consolas", 8)).pack(anchor="w", padx=14, pady=(0,14))

        tk.Frame(sidebar, bg=t["border"], height=1).pack(fill=tk.X, padx=10, pady=(0,12))

        tk.Label(sidebar, text="THÈMES", bg=t["sidebar"], fg=t["muted"],
                 font=("Consolas", 8, "bold")).pack(anchor="w", padx=14, pady=(0,6))

        for name, data in THEMES.items():
            is_active = (name == self.current_theme)
            tk.Button(
                sidebar,
                text=f"  {data['icon']}  {name}",
                anchor="w",
                bg=t["accent"] if is_active else t["sidebar"],
                fg=t["bg"] if is_active else t["text"],
                activebackground=t["border"],
                activeforeground=t["text"],
                font=("Consolas", 9, "bold" if is_active else "normal"),
                relief="flat", borderwidth=0, cursor="hand2",
                padx=8, pady=5,
                command=lambda n=name: self._switch_theme(n),
            ).pack(fill=tk.X, padx=8, pady=1)

        tk.Frame(sidebar, bg=t["border"], height=1).pack(fill=tk.X, padx=10, pady=(14,14))

        tk.Label(sidebar, text="sushiscan.net\nUsage personnel uniquement",
                 bg=t["sidebar"], fg=t["muted"], font=("Consolas", 7),
                 justify="left").pack(side=tk.BOTTOM, anchor="w", padx=14, pady=14)

        # ════ MAIN ════
        main = tk.Frame(outer, bg=t["bg"])
        main.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=22, pady=22)

        # Title row
        title_row = tk.Frame(main, bg=t["bg"])
        title_row.pack(fill=tk.X, pady=(0,16))
        tk.Label(title_row, text="Téléchargement", bg=t["bg"], fg=t["text"],
                 font=("Consolas", 17, "bold")).pack(side=tk.LEFT)
        tk.Label(title_row, textvariable=self.status_var, bg=t["bg"], fg=t["muted"],
                 font=("Consolas", 9)).pack(side=tk.LEFT, padx=(14,0), pady=(5,0))

        # ── URLs ──
        self._section(main, "🔗  URLs")
        grid = tk.Frame(main, bg=t["card"])
        grid.pack(fill=tk.X, pady=(0,10))
        grid.columnconfigure(1, weight=1)

        self._row(grid, "URL début", self.url_start_var, 0,
                  "https://sushiscan.net/nom-du-manga-volume-1/")
        self._row(grid, "URL fin (optionnel)", self.url_end_var, 1,
                  "Laisser vide pour un seul tome")
        tk.Label(grid,
                 text="  ℹ  ex: …/the-boys-edition-deluxe-volume-1/  ·  …/one-piece-chapitre-1100/",
                 bg=t["card"], fg=t["muted"], font=("Consolas", 8)
                 ).grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=(0,6))

        # ── Sortie ──
        self._section(main, "💾  Sortie")
        out_grid = tk.Frame(main, bg=t["card"])
        out_grid.pack(fill=tk.X, pady=(0,10))
        out_grid.columnconfigure(1, weight=1)

        self._row(out_grid, "Nom CBZ (optionnel)", self.cbz_name_var, 0,
                  "the-boys-volume-1  (sans .cbz)")

        folder_row = tk.Frame(out_grid, bg=t["card"])
        folder_row.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=6)
        tk.Label(folder_row, text="Dossier de sortie", bg=t["card"], fg=t["muted"],
                 font=("Consolas", 9), width=20, anchor="w").pack(side=tk.LEFT)
        tk.Entry(folder_row, textvariable=self.folder_var,
                 bg=t["entry_bg"], fg=t["text"], insertbackground=t["accent"],
                 relief="flat", font=("Consolas", 10), bd=5
                 ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6,6))
        tk.Button(folder_row, text="Parcourir…",
                  bg=t["border"], fg=t["text"],
                  activebackground=t["muted"], activeforeground=t["text"],
                  relief="flat", font=("Consolas", 9), cursor="hand2",
                  padx=10, pady=3, command=self._browse_folder
                  ).pack(side=tk.LEFT)

        # ── Options ──
        self._section(main, "⚙️  Options")
        opt = tk.Frame(main, bg=t["card"])
        opt.pack(fill=tk.X, pady=(0,10))

        tk.Label(opt, text="Pause entre chapitres (s) :", bg=t["card"], fg=t["muted"],
                 font=("Consolas", 9)).pack(side=tk.LEFT, padx=(10,0))
        ttk.Spinbox(opt, from_=5, to=300, textvariable=self.pause_var,
                    width=5).pack(side=tk.LEFT, padx=(6,24))
        tk.Checkbutton(opt,
                       text="Mode headless  (décocher si Cloudflare bloque)",
                       variable=self.headless_var,
                       bg=t["card"], fg=t["muted"],
                       selectcolor=t["entry_bg"],
                       activebackground=t["card"], activeforeground=t["text"],
                       font=("Consolas", 9), borderwidth=0
                       ).pack(side=tk.LEFT, pady=8)

        # ── Buttons ──
        btn_row = tk.Frame(main, bg=t["bg"])
        btn_row.pack(fill=tk.X, pady=(4,4))

        self.start_btn = tk.Button(btn_row, text="▶  Démarrer",
                                   bg=t["accent"], fg=t["bg"],
                                   activebackground=t["accent2"], activeforeground=t["bg"],
                                   font=("Consolas", 10, "bold"), relief="flat",
                                   cursor="hand2", padx=18, pady=8,
                                   command=self._start)
        self.start_btn.pack(side=tk.LEFT)

        self.stop_btn = tk.Button(btn_row, text="⏹  Arrêter",
                                  bg=t["card"], fg=t["text"],
                                  activebackground=t["border"], activeforeground=t["text"],
                                  font=("Consolas", 10), relief="flat",
                                  cursor="hand2", padx=14, pady=8,
                                  state=tk.DISABLED, command=self._stop)
        self.stop_btn.pack(side=tk.LEFT, padx=(8,0))

        self.continue_btn = tk.Button(btn_row, text="✅  Continuer",
                                      bg="#16a34a", fg="#ffffff",
                                      activebackground="#15803d", activeforeground="#ffffff",
                                      font=("Consolas", 10, "bold"), relief="flat",
                                      cursor="hand2", padx=18, pady=8,
                                      state=tk.DISABLED, command=self._continue)
        self.continue_btn.pack(side=tk.LEFT, padx=(8,0))

        # ── Progress ──
        tk.Label(main, textvariable=self.status_var, bg=t["bg"], fg=t["muted"],
                 font=("Consolas", 8)).pack(fill=tk.X, pady=(6,2))
        self.progress = ttk.Progressbar(main, mode="determinate")
        self.progress.pack(fill=tk.X, pady=(0,8))

        # ── Log ──
        self._section(main, "📋  Journal")
        self.log = scrolledtext.ScrolledText(
            main, bg=t["entry_bg"], fg=t["muted"],
            font=("Consolas", 9), relief="flat",
            wrap=tk.WORD, state=tk.DISABLED, height=10,
            insertbackground=t["accent"], selectbackground=t["border"])
        self.log.pack(fill=tk.BOTH, expand=True)
        self.log.tag_config("info", foreground=t["muted"])
        self.log.tag_config("ok",   foreground=t["ok"])
        self.log.tag_config("warn", foreground=t["warn"])
        self.log.tag_config("err",  foreground=t["err"])
        self.log.tag_config("step", foreground=t["step"])

    def _section(self, parent, title):
        """Section header bar."""
        t = self.theme
        bar = tk.Frame(parent, bg=t["card"])
        bar.pack(fill=tk.X, pady=(0,0))
        tk.Label(bar, text=title, bg=t["card"], fg=t["accent"],
                 font=("Consolas", 9, "bold")).pack(anchor="w", padx=10, pady=5)
        tk.Frame(parent, bg=t["border"], height=1).pack(fill=tk.X, pady=(0,0))

    def _row(self, grid, label, var, row, placeholder=""):
        """A label + entry row inside a grid frame."""
        t = self.theme
        tk.Label(grid, text=label, bg=t["card"], fg=t["muted"],
                 font=("Consolas", 9), width=22, anchor="w"
                 ).grid(row=row, column=0, sticky="w", padx=(10,0), pady=6)

        # Placeholder logic
        current = var.get()
        fg_color = t["muted"] if (not current or current == placeholder) else t["text"]
        if not current:
            var.set(placeholder)

        entry = tk.Entry(grid, textvariable=var,
                         bg=t["entry_bg"], fg=fg_color,
                         insertbackground=t["accent"],
                         relief="flat", font=("Consolas", 10), bd=5)
        entry.grid(row=row, column=1, sticky="ew", padx=(8,10), pady=6)

        def on_focus_in(e, v=var, en=entry, ph=placeholder):
            if v.get() == ph:
                v.set("")
                en.config(fg=t["text"])

        def on_focus_out(e, v=var, en=entry, ph=placeholder):
            if not v.get().strip():
                v.set(ph)
                en.config(fg=t["muted"])

        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

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
        # Never treat a real URL as a placeholder
        if val.startswith("http"):
            return val
        return "" if val == placeholder else val

    # ── Controls ────────────────────────────────────────────────────────────

    def _start(self):
        url = self._get_field(self.url_start_var,
                              "https://sushiscan.net/nom-du-manga-volume-1/")
        if not url.startswith("http"):
            messagebox.showerror("Erreur", "Entre une URL valide (commence par http).")
            return
        self.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.continue_btn.config(state=tk.DISABLED)
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
        self.root.after(0, lambda: self.continue_btn.config(state=tk.DISABLED))

    def _reset_buttons(self):
        def _do():
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.continue_btn.config(state=tk.DISABLED)
        self.root.after(0, _do)

    def _wait_continue(self, msg):
        self._log(f"⏳ {msg}", "warn")
        self._set_status(msg)
        self.root.after(0, lambda: self.continue_btn.config(state=tk.NORMAL))
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

        PH_START  = "https://sushiscan.net/nom-du-manga-volume-1/"
        PH_END    = "Laisser vide pour un seul tome"
        PH_CBZ    = "the-boys-volume-1  (sans .cbz)"

        url_start = self._get_field(self.url_start_var, PH_START)
        url_end   = self._get_field(self.url_end_var,   PH_END)
        cbz_name  = self._get_field(self.cbz_name_var,  PH_CBZ)
        out_dir   = self.folder_var.get()
        pause     = self.pause_var.get()
        headless  = self.headless_var.get()

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
        try:
            for idx, (chap_url, slug) in enumerate(entries):
                if not self.running:
                    break
                self._log(f"\n{'─'*50}", "info")
                self._log(f"📖 [{idx+1}/{len(entries)}] {slug}", "step")
                self._set_progress(int(idx / len(entries) * 100))
                imgs = self._download_entry(chap_url, slug, out_dir,
                                            pause if idx > 0 else 0)
                if imgs:
                    all_images[slug] = imgs
                    self._log(f"✅ {len(imgs)} pages.", "ok")
                else:
                    self._log(f"⚠️  Aucune image pour {slug}.", "warn")
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

        if all_images:
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

        self._wait_continue(
            "Étape 1/2 — Résous le captcha si nécessaire, puis clique Continuer."
        )
        if not self.running:
            return []

        self._try_vertical_mode()
        time.sleep(2)

        self._wait_continue(
            "Étape 2/2 — Attends que toutes les images soient visibles, puis clique Continuer."
        )
        if not self.running:
            return []

        img_urls = self._extract_images()
        if not img_urls:
            self._log("⚠️  Aucune image détectée.", "warn")
            return []

        self._log(f"🖼  {len(img_urls)} images trouvées.", "info")

        chap_dir = os.path.join(out_dir, "_sushi_tmp", slug)
        os.makedirs(chap_dir, exist_ok=True)

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
            ua = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36")

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
            els = self.driver.find_elements(
                By.CSS_SELECTOR,
                "#readerarea img, .reading-content img, .read-container img, "
                "#chapter-images img, .entry-content img"
            )
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

def main():
    root = tk.Tk()
    app = SushiScanDownloader(root)

    def on_close():
        if app.running:
            if not messagebox.askyesno("Quitter",
                    "Un téléchargement est en cours. Quitter quand même ?"):
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
