"""
Simple folder organizer with a Tkinter GUI.
- Lets the user pick a target folder (defaults to Downloads if present).
- Creates category folders and moves files based on extension.
- Groups images and videos inside a Media parent folder.
"""
from __future__ import annotations

import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Tuple
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Palettes
LIGHT_PALETTE = {
    "BG_APP": "#eef1f8",
    "SIDEBAR_BG": "#ffffff",
    "CARD_BG": "#ffffff",
    "CARD_DARK": "#0b1223",
    "ACCENT": "#2563eb",
    "ACCENT_GRADIENT_START": "#7c3aed",
    "ACCENT_GRADIENT_END": "#22d3ee",
    "TEXT_PRIMARY": "#0f172a",
    "TEXT_MUTED": "#556075",
    "SHADOW": "#d5d8e4",
}

DARK_PALETTE = {
    "BG_APP": "#0b1220",
    "SIDEBAR_BG": "#0f172a",
    "CARD_BG": "#111827",
    "CARD_DARK": "#0b1223",
    "ACCENT": "#22d3ee",
    "ACCENT_GRADIENT_START": "#312e81",
    "ACCENT_GRADIENT_END": "#0ea5e9",
    "TEXT_PRIMARY": "#e5e7eb",
    "TEXT_MUTED": "#94a3b8",
    "SHADOW": "#0f172a",
}

# Active palette (mutated by set_palette)
BG_APP = LIGHT_PALETTE["BG_APP"]
SIDEBAR_BG = LIGHT_PALETTE["SIDEBAR_BG"]
CARD_BG = LIGHT_PALETTE["CARD_BG"]
CARD_DARK = LIGHT_PALETTE["CARD_DARK"]
ACCENT = LIGHT_PALETTE["ACCENT"]
ACCENT_GRADIENT_START = LIGHT_PALETTE["ACCENT_GRADIENT_START"]
ACCENT_GRADIENT_END = LIGHT_PALETTE["ACCENT_GRADIENT_END"]
TEXT_PRIMARY = LIGHT_PALETTE["TEXT_PRIMARY"]
TEXT_MUTED = LIGHT_PALETTE["TEXT_MUTED"]
SHADOW = LIGHT_PALETTE["SHADOW"]


def set_palette(palette: Dict[str, str]) -> None:
    global BG_APP, SIDEBAR_BG, CARD_BG, CARD_DARK, ACCENT, ACCENT_GRADIENT_START, ACCENT_GRADIENT_END, TEXT_PRIMARY, TEXT_MUTED, SHADOW
    BG_APP = palette["BG_APP"]
    SIDEBAR_BG = palette["SIDEBAR_BG"]
    CARD_BG = palette["CARD_BG"]
    CARD_DARK = palette["CARD_DARK"]
    ACCENT = palette["ACCENT"]
    ACCENT_GRADIENT_START = palette["ACCENT_GRADIENT_START"]
    ACCENT_GRADIENT_END = palette["ACCENT_GRADIENT_END"]
    TEXT_PRIMARY = palette["TEXT_PRIMARY"]
    TEXT_MUTED = palette["TEXT_MUTED"]
    SHADOW = palette["SHADOW"]

# History file location
HISTORY_FILE = Path.home() / "Documents" / "Technolize" / "organizer_history.json"

# Category definition: destination folder -> list of extensions
CATEGORY_MAP: Dict[str, Iterable[str]] = {
    # Document family in their own subfolders
    "Documents/Excel": [".xls", ".xlsx", ".xlsm", ".xlsb", ".xltx", ".csv"],
    "Documents/Word": [".doc", ".docx", ".odt", ".rtf"],
    "Documents/PDF": [".pdf"],
    "Documents/Text": [".txt"],
    "Media/Images": [
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".tiff",
        ".webp",
        ".heic",
    ],
    "Media/Videos": [
        ".mp4",
        ".mov",
        ".avi",
        ".mkv",
        ".wmv",
        ".flv",
        ".webm",
        ".m4v",
    ],
}

# Move pre-existing top-level buckets into the Documents parent when found
LEGACY_FOLDER_REMAP: Dict[str, str] = {
    "Excel": "Documents/Excel",
    "Word": "Documents/Word",
    "PDF": "Documents/PDF",
    "Text": "Documents/Text",
}

# Fallback bucket for uncategorized files
OTHER_FOLDER = "Other"


def resolve_destination(file_path: Path) -> Path | None:
    """Return destination subpath relative to base folder for a given file."""
    ext = file_path.suffix.lower()
    for dest, extensions in CATEGORY_MAP.items():
        if ext in extensions:
            return Path(dest)
    return None


def ensure_unique_path(target: Path) -> Path:
    """Avoid overwriting existing files by appending a counter."""
    if not target.exists():
        return target
    stem, suffix = target.stem, target.suffix
    parent = target.parent
    counter = 1
    while True:
        candidate = parent / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def ensure_unique_dir(target: Path) -> Path:
    """Avoid overwriting existing directories by appending a counter."""
    if not target.exists():
        return target
    parent = target.parent
    counter = 1
    while True:
        candidate = parent / f"{target.name} ({counter})"
        if not candidate.exists():
            return candidate
        counter += 1


def organize_folder(base_folder: Path) -> List[Tuple[Path, Path]]:
    """Organize files in base_folder. Returns list of (src, dest) moves."""
    moves: List[Tuple[Path, Path]] = []
    for entry in base_folder.iterdir():
        if entry.is_dir():
            continue
        dest_subpath = resolve_destination(entry)
        dest_root = dest_subpath if dest_subpath is not None else Path(OTHER_FOLDER)
        dest_folder = base_folder / dest_root
        dest_folder.mkdir(parents=True, exist_ok=True)
        target = ensure_unique_path(dest_folder / entry.name)
        shutil.move(str(entry), target)
        moves.append((entry, target))
    relocate_legacy_folders(base_folder, moves)
    return moves


def relocate_legacy_folders(base_folder: Path, moves: List[Tuple[Path, Path]]) -> None:
    """If legacy top-level folders exist (Excel, Word, PDF, Text), move their contents under Documents/*."""
    for legacy_name, dest_rel in LEGACY_FOLDER_REMAP.items():
        src_dir = base_folder / legacy_name
        if not src_dir.exists() or not src_dir.is_dir():
            continue
        dest_dir = base_folder / Path(dest_rel)
        dest_dir.mkdir(parents=True, exist_ok=True)
        for item in list(src_dir.iterdir()):
            if item.is_dir():
                target_dir = ensure_unique_dir(dest_dir / item.name)
                shutil.move(str(item), target_dir)
                moves.append((item, target_dir))
            else:
                target_file = ensure_unique_path(dest_dir / item.name)
                shutil.move(str(item), target_file)
                moves.append((item, target_file))
        # Clean up empty legacy folder
        try:
            src_dir.rmdir()
        except OSError:
            pass


class OrganizerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Technolize Organizer")
        self.root.geometry("1180x740")
        # Center the window on screen
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 1180
        window_height = 740
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(960, 640)
        self.theme_mode = "light"
        set_palette(LIGHT_PALETTE)
        self.root.configure(bg=BG_APP)
        self._resize_job: str | None = None

        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.folder_var = tk.StringVar(value=str(self.default_downloads()))

        self.nav_buttons: dict[str, tk.Button] = {}
        self.main_content: tk.Frame | None = None

        self.history: list[dict] = []
        self.history_tree: ttk.Treeview | None = None
        self.history_file = HISTORY_FILE

        self.hero_canvas: tk.Canvas | None = None

        self.load_history()
        self.apply_styles()
        self.root.configure(bg=BG_APP)
        self.build_ui()
        self.root.bind("<Configure>", self.on_resize)

    def default_downloads(self) -> Path:
        downloads = Path.home() / "Downloads"
        return downloads if downloads.exists() else Path.home()

    def build_ui(self) -> None:
        root_container = tk.Frame(self.root, bg=BG_APP)
        root_container.pack(fill="both", expand=True)

        # Sidebar
        sidebar = ttk.Frame(root_container, style="Sidebar.TFrame", padding=18)
        sidebar.pack(side="left", fill="y")
        tk.Label(sidebar, text="Technolize", font=("Segoe UI", 16, "bold"), fg=TEXT_PRIMARY, bg=SIDEBAR_BG).pack(anchor="w", pady=(0, 12))
        nav_items = [
            ("Dashboard", self.render_dashboard),
            ("History", self.render_history),
            ("How it works", lambda: self.render_section("How it works", "See what the organizer does before you run it.")),
            ("Settings", self.render_settings),
        ]
        for label, handler in nav_items:
            self.nav_item(sidebar, label, command=handler)

        # Main area
        main = tk.Frame(root_container, bg=BG_APP, padx=20, pady=20)
        main.pack(side="right", fill="both", expand=True)

        # Header
        header = tk.Frame(main, bg=BG_APP)
        header.pack(fill="x")
        tk.Label(header, text="Overview", font=("Segoe UI", 10), fg=TEXT_MUTED, bg=BG_APP).pack(anchor="w")
        self.header_title = tk.Label(header, text="Dashboard", font=("Segoe UI", 22, "bold"), fg=TEXT_PRIMARY, bg=BG_APP)
        self.header_title.pack(anchor="w", pady=(2, 12))

        self.content_container = tk.Frame(main, bg=BG_APP)
        self.content_container.pack(fill="both", expand=True)

        self.render_dashboard()

    def choose_folder(self) -> None:
        selected = filedialog.askdirectory(title="Select folder to organize")
        if selected:
            self.folder_var.set(selected)

    def on_run(self) -> None:
        base = Path(self.folder_var.get()).expanduser()
        if not base.exists() or not base.is_dir():
            messagebox.showerror("Invalid folder", "Please select a valid folder.")
            return
        moves = organize_folder(base)
        self.write_log(moves)
        self.add_history(base, moves)
        messagebox.showinfo("Done", f"Moved {len(moves)} file(s).")

    def write_log(self, moves: List[Tuple[Path, Path]]) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", tk.END)
        if not moves:
            self.log.insert(tk.END, "No files to move.\n")
        else:
            for src, dest in moves:
                self.log.insert(tk.END, f"{src.name} -> {dest.relative_to(Path(self.folder_var.get()))}\n")
        self.log.configure(state="disabled")

    def nav_item(self, parent: tk.Widget, text: str, muted: bool = False, command=None) -> None:
        fg = TEXT_MUTED if muted else TEXT_PRIMARY
        btn = tk.Button(
            parent,
            text=text,
            font=("Segoe UI", 10, "bold" if not muted else "normal"),
            fg=fg,
            bg=SIDEBAR_BG,
            activebackground=SIDEBAR_BG,
            activeforeground=ACCENT,
            relief="flat",
            bd=0,
            padx=6,
            pady=6,
            anchor="w",
            command=lambda: self.on_nav_click(text, command),
        )
        btn.pack(fill="x", pady=2)
        if not muted:
            self.nav_buttons[text] = btn

    def on_nav_click(self, label: str, handler) -> None:
        self.set_active_nav(label)
        if callable(handler):
            handler()

    def set_active_nav(self, label: str) -> None:
        self.active_view = label
        for name, btn in self.nav_buttons.items():
            is_active = name == label
            btn.configure(
                fg=(ACCENT if is_active else TEXT_PRIMARY),
                font=("Segoe UI", 10, "bold" if is_active else "normal"),
            )
        if hasattr(self, "header_title") and self.header_title:
            self.header_title.configure(text=label)

    def clear_content(self) -> None:
        for child in self.content_container.winfo_children():
            child.destroy()
        self.hero_canvas = None
        self.history_tree = None

    def render_view(self, name: str) -> None:
        if name == "Dashboard":
            self.render_dashboard()
        elif name == "History":
            self.render_history()
        elif name == "How it works":
            self.render_section("How it works", "See what the organizer does before you run it.")
        elif name == "Settings":
            self.render_settings()
        else:
            self.render_dashboard()

    def render_dashboard(self) -> None:
        self.clear_content()
        self.set_active_nav("Dashboard")

        hero_container = tk.Frame(self.content_container, bg=BG_APP)
        hero_container.pack(fill="x")
        self.hero_canvas = tk.Canvas(hero_container, height=200, highlightthickness=0, bd=0, bg=BG_APP)
        self.hero_canvas.pack(fill="x", expand=True)
        self.draw_hero_content()

        last_run = self.history[0] if self.history else None
        last_label = last_run["label"] if last_run else "No runs yet"
        last_count = len(last_run["moves"]) if last_run else 0
        last_base = last_run["base"] if last_run else None
        last_base_text = last_base.name if last_base else "—"

        cards = tk.Frame(self.content_container, bg=BG_APP)
        cards.pack(fill="x", pady=(14, 4))
        metrics = [
            ("Last run", last_label),
            ("Files moved", f"{last_count}"),
            ("Folder", last_base_text),
        ]
        for title, value in metrics:
            frame = ttk.Frame(cards, padding=14, style="Card.TFrame")
            frame.pack(side="left", fill="x", expand=True, padx=6)
            tk.Label(frame, text=title, font=("Segoe UI", 11, "bold"), fg=TEXT_PRIMARY, bg=CARD_BG).pack(anchor="w")
            tk.Label(frame, text=value, font=("Segoe UI", 10), fg=TEXT_MUTED, bg=CARD_BG).pack(anchor="w", pady=(2, 0))

        form_card = ttk.Frame(self.content_container, padding=18, style="Card.TFrame")
        form_card.pack(fill="both", expand=True, pady=(10, 0))

        top_row = tk.Frame(form_card, bg=CARD_BG)
        top_row.pack(fill="x")
        tk.Label(top_row, text="Organize a folder", font=("Segoe UI", 12, "bold"), fg=TEXT_PRIMARY, bg=CARD_BG).pack(anchor="w")
        tk.Label(top_row, text="Pick a folder, run organize, then check History to verify moves.", font=("Segoe UI", 10), fg=TEXT_MUTED, bg=CARD_BG).pack(anchor="w", pady=(2, 10))

        input_row = tk.Frame(form_card, bg=CARD_BG)
        input_row.pack(fill="x", pady=(0, 10))
        ttk.Entry(input_row, textvariable=self.folder_var, font=("Segoe UI", 11)).pack(side="left", fill="x", expand=True, ipady=8)
        self.rounded_button(input_row, "Browse", self.choose_folder, fill=ACCENT, hover=ACCENT, fg="#ffffff").pack(side="left", padx=(10, 0))
        self.rounded_button(input_row, "Organize now", self.on_run, fill=ACCENT, hover=ACCENT, fg="#ffffff").pack(side="left", padx=(10, 0))

        btn_row = tk.Frame(form_card, bg=CARD_BG)
        btn_row.pack(fill="x", pady=(0, 6))
        self.rounded_button(btn_row, "View History", self.render_history, fill=SHADOW, hover=ACCENT, fg=TEXT_PRIMARY).pack(side="left", padx=(6, 6))
        self.rounded_button(btn_row, "How it works", lambda: self.render_section("How it works", "See what the organizer does before you run it."), fill=SHADOW, hover=ACCENT, fg=TEXT_PRIMARY).pack(side="left", padx=(6, 6))
        self.rounded_button(btn_row, "Settings", self.render_settings, fill=SHADOW, hover=ACCENT, fg=TEXT_PRIMARY).pack(side="left", padx=(6, 6))

        log_title = tk.Label(form_card, text="Activity Log", font=("Segoe UI", 12, "bold"), fg=TEXT_PRIMARY, bg=CARD_BG)
        log_title.pack(anchor="w", pady=(6, 6))

        self.log = tk.Text(
            form_card,
            height=10,
            wrap="word",
            state="disabled",
            bg=CARD_DARK,
            fg="#e2e8f0",
            insertbackground="#e2e8f0",
            relief="flat",
            padx=12,
            pady=12,
        )
        self.log.pack(fill="both", expand=True)

        footer = tk.Label(
            self.content_container,
            text="Docs land in Documents/Excel, Documents/Word, Documents/PDF, Documents/Text. Media goes to Media/Images and Media/Videos. Everything else goes to Other.",
            fg=TEXT_MUTED,
            bg=BG_APP,
            wraplength=820,
        )
        footer.pack(anchor="w", pady=(10, 0))

    def show_placeholder(self, label: str) -> None:
        self.clear_content()
        self.set_active_nav(label)
        placeholder = ttk.Frame(self.content_container, padding=30, style="Card.TFrame")
        placeholder.pack(fill="both", expand=True)
        tk.Label(placeholder, text=f"{label} coming soon", font=("Segoe UI", 14, "bold"), fg=TEXT_PRIMARY, bg=CARD_BG).pack(anchor="center", pady=10)
        tk.Label(placeholder, text="Click Dashboard to return", font=("Segoe UI", 11), fg=TEXT_MUTED, bg=CARD_BG).pack(anchor="center")

    def render_section(self, label: str, description: str) -> None:
        self.clear_content()
        self.set_active_nav(label)

        tk.Label(self.content_container, text=description, font=("Segoe UI", 11), fg=TEXT_MUTED, bg=BG_APP).pack(anchor="w", pady=(0, 10))

        if label == "How it works":
            self.render_how_it_works()
            return

        card = ttk.Frame(self.content_container, padding=18, style="Card.TFrame")
        card.pack(fill="both", expand=True)
        tk.Label(card, text=f"{label} panel", font=("Segoe UI", 12, "bold"), fg=TEXT_PRIMARY, bg=CARD_BG).pack(anchor="w")
        tk.Label(card, text="Feature controls will appear here.", font=("Segoe UI", 10), fg=TEXT_MUTED, bg=CARD_BG).pack(anchor="w", pady=(4, 10))

        action_row = tk.Frame(card, bg=CARD_BG)
        action_row.pack(fill="x", pady=(0, 8))
        self.rounded_button(action_row, "Back to Dashboard", self.render_dashboard, fill=ACCENT, hover=ACCENT, fg="#ffffff").pack(side="left", padx=(0, 10))
        self.rounded_button(action_row, "View History", self.render_history, fill=SHADOW, hover=ACCENT, fg=TEXT_PRIMARY).pack(side="left")

    def render_history(self) -> None:
        self.clear_content()
        self.set_active_nav("History")

        header = tk.Frame(self.content_container, bg=BG_APP)
        header.pack(fill="x", pady=(0, 12))
        tk.Label(header, text="History", font=("Segoe UI", 18, "bold"), fg=TEXT_PRIMARY, bg=BG_APP).pack(anchor="w")
        tk.Label(header, text="Recent organization runs and moved files", font=("Segoe UI", 11), fg=TEXT_MUTED, bg=BG_APP).pack(anchor="w")

        self.build_history_section(self.content_container)

        footer = tk.Label(
            self.content_container,
            text=f"History is saved to {self.history_file}.",
            fg=TEXT_MUTED,
            bg=BG_APP,
            wraplength=820,
        )
        footer.pack(anchor="w", pady=(10, 0))

    def render_settings(self) -> None:
        self.clear_content()
        self.set_active_nav("Settings")

        tk.Label(self.content_container, text="Preferences", font=("Segoe UI", 18, "bold"), fg=TEXT_PRIMARY, bg=BG_APP).pack(anchor="w")
        tk.Label(self.content_container, text="Switch theme for the entire app.", font=("Segoe UI", 11), fg=TEXT_MUTED, bg=BG_APP).pack(anchor="w", pady=(2, 12))

        card = ttk.Frame(self.content_container, padding=18, style="Card.TFrame")
        card.pack(fill="x")
        tk.Label(card, text="Theme", font=("Segoe UI", 12, "bold"), fg=TEXT_PRIMARY, bg=CARD_BG).pack(anchor="w")
        tk.Label(card, text="Toggle between light and dark.", font=("Segoe UI", 10), fg=TEXT_MUTED, bg=CARD_BG).pack(anchor="w", pady=(2, 8))
        toggle_row = tk.Frame(card, bg=CARD_BG)
        toggle_row.pack(anchor="w", pady=(0, 4))
        self.build_theme_toggle(toggle_row)

    def add_history(self, base: Path, moves: List[Tuple[Path, Path]]) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "label": f"{timestamp} • {base}",
            "moves": moves,
            "base": base,
        }
        self.history.insert(0, entry)
        if len(self.history) > 20:
            self.history = self.history[:20]
        self.save_history()
        self.refresh_history_view()

    def refresh_history_view(self) -> None:
        if not self.history_tree:
            return
        self.history_tree.delete(*self.history_tree.get_children())
        if not self.history:
            self.history_tree.insert("", "end", text="No runs yet", values=("",))
            return
        for run in self.history:
            summary = f"{run['label']} • {len(run['moves'])} files"
            parent = self.history_tree.insert("", "end", text=summary, values=("",))
            for src, dest in run["moves"]:
                try:
                    rel = dest.relative_to(run["base"])
                except Exception:
                    rel = dest
                self.history_tree.insert(parent, "end", text=src.name, values=(str(rel),))

    def render_organization_panel(self) -> None:
        cards = tk.Frame(self.content_container, bg=BG_APP)
        cards.pack(fill="x", pady=(0, 12))

        summary = ttk.Frame(cards, padding=14, style="Card.TFrame")
        summary.pack(side="left", fill="x", expand=True, padx=6)
        tk.Label(summary, text="Quick organize", font=("Segoe UI", 12, "bold"), fg=TEXT_PRIMARY, bg=CARD_BG).pack(anchor="w")
        tk.Label(summary, text="Point to a folder and run. We keep files safe (no overwrite).", font=("Segoe UI", 10), fg=TEXT_MUTED, bg=CARD_BG, wraplength=260).pack(anchor="w", pady=(4, 6))
        self.rounded_button(summary, "Browse folder", self.choose_folder, fill=ACCENT, hover=ACCENT, fg="#ffffff").pack(anchor="w", pady=(0, 6))
        self.rounded_button(summary, "Organize now", self.on_run, fill=ACCENT, hover=ACCENT, fg="#ffffff").pack(anchor="w")

        categories = ttk.Frame(cards, padding=14, style="Card.TFrame")
        categories.pack(side="left", fill="x", expand=True, padx=6)
        tk.Label(categories, text="Rules in use", font=("Segoe UI", 12, "bold"), fg=TEXT_PRIMARY, bg=CARD_BG).pack(anchor="w")
        tk.Label(categories, text="Documents → Documents/*  |  Media → Media/*  |  Everything else → Other", font=("Segoe UI", 10), fg=TEXT_MUTED, bg=CARD_BG, wraplength=280).pack(anchor="w", pady=(4, 6))
        tk.Label(categories, text="Documents: Excel, Word, PDF, Text", font=("Segoe UI", 10), fg=TEXT_MUTED, bg=CARD_BG).pack(anchor="w")
        tk.Label(categories, text="Media: Images, Videos", font=("Segoe UI", 10), fg=TEXT_MUTED, bg=CARD_BG).pack(anchor="w")

        actions = ttk.Frame(cards, padding=14, style="Card.TFrame")
        actions.pack(side="left", fill="x", expand=True, padx=6)
        tk.Label(actions, text="Shortcuts", font=("Segoe UI", 12, "bold"), fg=TEXT_PRIMARY, bg=CARD_BG).pack(anchor="w")
        tk.Label(actions, text="Open the target folder or jump to your latest history entry.", font=("Segoe UI", 10), fg=TEXT_MUTED, bg=CARD_BG, wraplength=260).pack(anchor="w", pady=(4, 6))
        self.rounded_button(actions, "View History", self.render_history, fill=SHADOW, hover=ACCENT, fg=TEXT_PRIMARY).pack(anchor="w", pady=(0, 6))
        self.rounded_button(actions, "Back to Dashboard", self.render_dashboard, fill=SHADOW, hover=ACCENT, fg=TEXT_PRIMARY).pack(anchor="w")

        # Reuse the existing form + log below
        card = ttk.Frame(self.content_container, padding=18, style="Card.TFrame")
        card.pack(fill="both", expand=True, pady=(10, 0))

        top_row = tk.Frame(card, bg=CARD_BG)
        top_row.pack(fill="x")
        tk.Label(top_row, text="Organize a folder", font=("Segoe UI", 12, "bold"), fg=TEXT_PRIMARY, bg=CARD_BG).pack(anchor="w")
        tk.Label(top_row, text="Choose a path and run organize to sort files by type.", font=("Segoe UI", 10), fg=TEXT_MUTED, bg=CARD_BG).pack(anchor="w", pady=(2, 10))

        input_row = tk.Frame(card, bg=CARD_BG)
        input_row.pack(fill="x", pady=(0, 12))
        ttk.Entry(input_row, textvariable=self.folder_var, font=("Segoe UI", 11)).pack(side="left", fill="x", expand=True, ipady=8)
        self.rounded_button(input_row, "Browse", self.choose_folder, fill=ACCENT, hover=ACCENT, fg="#ffffff").pack(side="left", padx=(10, 0))
        self.rounded_button(input_row, "Organize now", self.on_run, fill=ACCENT, hover=ACCENT, fg="#ffffff").pack(side="left", padx=(10, 0))

        log_title = tk.Label(card, text="Activity Log", font=("Segoe UI", 12, "bold"), fg=TEXT_PRIMARY, bg=CARD_BG)
        log_title.pack(anchor="w", pady=(6, 6))

        self.log = tk.Text(
            card,
            height=10,
            wrap="word",
            state="disabled",
            bg=CARD_DARK,
            fg="#e2e8f0",
            insertbackground="#e2e8f0",
            relief="flat",
            padx=12,
            pady=12,
        )
        self.log.pack(fill="both", expand=True)

    def render_how_it_works(self) -> None:
        info = ttk.Frame(self.content_container, padding=18, style="Card.TFrame")
        info.pack(fill="both", expand=True, pady=(0, 10))
        tk.Label(info, text="What happens when you click organize", font=("Segoe UI", 12, "bold"), fg=TEXT_PRIMARY, bg=CARD_BG).pack(anchor="w")
        steps = [
            "We scan only the top level of the selected folder (no deep recursion).",
            "We route files by extension into Documents/* and Media/*, anything else goes to Other.",
            "We never overwrite: files/folders get '(1)', '(2)', … if names collide.",
            "Legacy Excel/Word/PDF/Text folders are folded into Documents/* automatically.",
        ]
        for step in steps:
            tk.Label(info, text=f"• {step}", font=("Segoe UI", 10), fg=TEXT_MUTED, bg=CARD_BG, wraplength=780, justify="left").pack(anchor="w", pady=(2, 0))

        rules = ttk.Frame(self.content_container, padding=18, style="Card.TFrame")
        rules.pack(fill="both", expand=True, pady=(8, 10))
        tk.Label(rules, text="Routing rules", font=("Segoe UI", 12, "bold"), fg=TEXT_PRIMARY, bg=CARD_BG).pack(anchor="w")
        tk.Label(rules, text="Documents → Documents/Excel, Documents/Word, Documents/PDF, Documents/Text", font=("Segoe UI", 10), fg=TEXT_MUTED, bg=CARD_BG, wraplength=820).pack(anchor="w", pady=(4, 2))
        tk.Label(rules, text="Media → Media/Images, Media/Videos", font=("Segoe UI", 10), fg=TEXT_MUTED, bg=CARD_BG).pack(anchor="w")
        tk.Label(rules, text="Other → Other", font=("Segoe UI", 10), fg=TEXT_MUTED, bg=CARD_BG).pack(anchor="w")

        actions = ttk.Frame(self.content_container, padding=18, style="Card.TFrame")
        actions.pack(fill="both", expand=True, pady=(8, 0))
        tk.Label(actions, text="Try it", font=("Segoe UI", 12, "bold"), fg=TEXT_PRIMARY, bg=CARD_BG).pack(anchor="w")
        tk.Label(actions, text="Pick a folder, run organize, then review the History tab to see moves.", font=("Segoe UI", 10), fg=TEXT_MUTED, bg=CARD_BG, wraplength=820).pack(anchor="w", pady=(4, 10))
        button_row = tk.Frame(actions, bg=CARD_BG)
        button_row.pack(fill="x")
        self.rounded_button(button_row, "Go to Dashboard", self.render_dashboard, fill=ACCENT, hover=ACCENT, fg="#ffffff").pack(side="left", padx=(0, 10))
        self.rounded_button(button_row, "View History", self.render_history, fill=SHADOW, hover=ACCENT, fg=TEXT_PRIMARY).pack(side="left")

    def save_history(self) -> None:
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            serializable = []
            for run in self.history:
                serializable.append(
                    {
                        "label": run.get("label", ""),
                        "base": str(run.get("base", "")),
                        "moves": [{"src": str(src), "dest": str(dest)} for src, dest in run.get("moves", [])],
                    }
                )
            payload = {
                "theme": self.theme_mode,
                "history": serializable,
            }
            with self.history_file.open("w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2)
        except Exception:
            pass

    def apply_styles(self) -> None:
        self.style.configure(
            "TButton",
            padding=10,
            font=("Segoe UI", 10, "bold"),
            borderwidth=0,
            relief="flat",
            background=SHADOW,
            foreground=TEXT_PRIMARY,
        )
        self.style.configure(
            "Treeview",
            background=CARD_BG,
            fieldbackground=CARD_BG,
            foreground=TEXT_PRIMARY,
            rowheight=26,
            bordercolor=CARD_BG,
            borderwidth=0,
        )
        self.style.configure(
            "Treeview.Heading",
            background=SIDEBAR_BG,
            foreground=TEXT_PRIMARY,
            font=("Segoe UI", 10, "bold"),
            bordercolor=SIDEBAR_BG,
            borderwidth=0,
        )
        self.style.map(
            "Treeview",
            background=[["selected", ACCENT]],
            foreground=[["selected", "#ffffff"]],
        )
        self.style.configure("TLabel", padding=4, foreground=TEXT_PRIMARY, background=CARD_BG)
        self.style.configure("Card.TFrame", relief="flat", background=CARD_BG)
        self.style.configure("Sidebar.TFrame", relief="flat", background=SIDEBAR_BG)
        self.style.configure(
            "Accent.TButton",
            background=ACCENT,
            foreground="#ffffff",
            borderwidth=0,
            relief="flat",
            padding=(14, 8),
        )
        self.style.map("Accent.TButton", background=[["active", ACCENT]])

        # Rounded look by adjusting layout element border
        self.style.layout(
            "Rounded.TButton",
            [
                ("Button.focus",
                 {"children": [
                     ("Button.border",
                      {"border": 0, "children": [
                          ("Button.padding", {"children": [("Button.label", {"side": "left", "expand": 1})]})
                      ]})
                 ]})
            ],
        )
        self.style.configure(
            "Rounded.TButton",
            padding=(14, 8),
            relief="flat",
            borderwidth=0,
            background=CARD_BG,
            foreground=TEXT_PRIMARY,
        )
        self.style.map("Rounded.TButton", background=[["active", SHADOW]])

    def rounded_button(self, parent: tk.Widget, text: str, command, fill: str | None = None, hover: str | None = None, fg: str | None = None, bg: str | None = None) -> tk.Canvas:
        fill = fill or CARD_BG
        hover = hover or SHADOW
        fg = fg or TEXT_PRIMARY
        canvas_bg = bg or parent["bg"]
        radius = 16
        height = 36
        width = max(90, 12 * len(text) + 24)
        canvas = tk.Canvas(parent, width=width, height=height, bd=0, highlightthickness=0, bg=canvas_bg)

        def draw(color: str) -> None:
            canvas.delete("all")
            r = radius
            x0, y0, x1, y1 = 2, 2, width - 2, height - 2
            # Rounded pill
            canvas.create_oval(x0, y0, x0 + 2 * r, y0 + 2 * r, outline=color, fill=color)
            canvas.create_oval(x1 - 2 * r, y0, x1, y0 + 2 * r, outline=color, fill=color)
            canvas.create_rectangle(x0 + r, y0, x1 - r, y0 + 2 * r, outline=color, fill=color)
            canvas.create_text(width / 2, height / 2, text=text, fill=fg, font=("Segoe UI", 10, "bold"))

        def on_enter(_event: tk.Event) -> None:
            draw(hover)

        def on_leave(_event: tk.Event) -> None:
            draw(fill)

        def on_click(_event: tk.Event) -> None:
            if callable(command):
                command()

        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)
        canvas.bind("<Button-1>", on_click)
        draw(fill)
        return canvas

    def build_theme_toggle(self, parent: tk.Widget) -> None:
        track_w, track_h = 70, 32
        radius = 14
        canvas = tk.Canvas(parent, width=track_w, height=track_h, bd=0, highlightthickness=0, bg=CARD_BG)
        canvas.pack(anchor="w")

        def draw() -> None:
            canvas.delete("all")
            is_on = self.theme_mode == "dark"
            track_color = ACCENT if is_on else "#cbd5e1"
            knob_color = "#ffffff" if is_on else "#0f172a"
            text_color = "#0b1223" if not is_on else "#0b1223"
            label_text = "ON" if is_on else "OFF"

            # pill track (two ovals + rect for rounded ends)
            canvas.create_oval(2, 2, 2 + 2 * radius, 2 + 2 * radius, outline=track_color, fill=track_color)
            canvas.create_oval(track_w - 2 - 2 * radius, 2, track_w - 2, 2 + 2 * radius, outline=track_color, fill=track_color)
            canvas.create_rectangle(2 + radius, 2, track_w - 2 - radius, 2 + 2 * radius, outline=track_color, fill=track_color)

            knob_x0 = track_w - 2 - 2 * radius - 2 if is_on else 4
            knob_x1 = knob_x0 + 2 * radius - 2
            canvas.create_oval(knob_x0, 4, knob_x1, track_h - 4, outline=knob_color, fill=knob_color)
            canvas.create_text(track_w / 2, track_h / 2, text=label_text, fill=text_color, font=("Segoe UI", 10, "bold"))

        def on_click(_event: tk.Event) -> None:
            self.toggle_theme()

        canvas.bind("<Button-1>", on_click)
        draw()

    def load_history(self) -> None:
        if not self.history_file.exists():
            self.history = []
            return
        try:
            data = json.loads(self.history_file.read_text(encoding="utf-8"))
            raw_runs = []
            stored_theme = None

            if isinstance(data, dict):
                raw_runs = data.get("history", []) if isinstance(data.get("history", []), list) else []
                stored_theme = data.get("theme")
            elif isinstance(data, list):
                # Backward compatibility with older format
                raw_runs = data

            loaded: list[dict] = []
            for run in raw_runs:
                base = Path(run.get("base", "")) if run.get("base") else Path.home()
                moves_list = []
                for mv in run.get("moves", []):
                    try:
                        moves_list.append((Path(mv.get("src", "")), Path(mv.get("dest", ""))))
                    except Exception:
                        continue
                loaded.append({"label": run.get("label", ""), "base": base, "moves": moves_list})

            self.history = loaded[:20]

            if stored_theme in ("light", "dark"):
                self.theme_mode = stored_theme
                set_palette(DARK_PALETTE if self.theme_mode == "dark" else LIGHT_PALETTE)
        except Exception:
            self.history = []

    def toggle_theme(self) -> None:
        self.theme_mode = "dark" if self.theme_mode == "light" else "light"
        set_palette(DARK_PALETTE if self.theme_mode == "dark" else LIGHT_PALETTE)
        self.apply_styles()
        self.root.configure(bg=BG_APP)
        self.rebuild_ui()
        self.save_history()

    def rebuild_ui(self) -> None:
        current = getattr(self, "active_view", "Dashboard")
        for child in self.root.winfo_children():
            child.destroy()
        self.nav_buttons = {}
        self.content_container = None
        self.hero_canvas = None
        self.history_tree = None
        self.build_ui()
        self.render_view(current)

    def build_history_section(self, parent: tk.Widget) -> None:
        history_card = ttk.Frame(parent, padding=18, style="Card.TFrame")
        history_card.pack(fill="both", expand=True, pady=(14, 0))
        tk.Label(history_card, text="Organization History", font=("Segoe UI", 12, "bold"), fg=TEXT_PRIMARY, bg=CARD_BG).pack(anchor="w")
        tk.Label(history_card, text="Recent file moves grouped by run", font=("Segoe UI", 10), fg=TEXT_MUTED, bg=CARD_BG).pack(anchor="w", pady=(2, 8))

        self.history_tree = ttk.Treeview(history_card, columns=("destination",), show="tree headings", height=10)
        self.history_tree.heading("#0", text="Item")
        self.history_tree.heading("destination", text="Destination")
        self.history_tree.column("destination", width=420, anchor="w")
        self.history_tree.pack(fill="both", expand=True)
        self.refresh_history_view()

    def draw_gradient(self, canvas: tk.Canvas, start: str, end: str) -> None:
        canvas.delete("grad")
        width = max(canvas.winfo_width(), 800)
        height = int(canvas["height"])
        steps = max(width, 300)
        r1, g1, b1 = canvas.winfo_rgb(start)
        r2, g2, b2 = canvas.winfo_rgb(end)
        for i in range(steps):
            r = int(r1 + (r2 - r1) * i / steps)
            g = int(g1 + (g2 - g1) * i / steps)
            b = int(b1 + (b2 - b1) * i / steps)
            color = f"#{r >> 8:02x}{g >> 8:02x}{b >> 8:02x}"
            x0 = i * width / steps
            x1 = (i + 1) * width / steps
            canvas.create_rectangle(x0, 0, x1, height, outline="", fill=color, tags="grad")

    def draw_hero_content(self) -> None:
        if not self.hero_canvas:
            return
        self.hero_canvas.delete("all")
        self.draw_gradient(self.hero_canvas, ACCENT_GRADIENT_START, ACCENT_GRADIENT_END)
        self.hero_canvas.create_text(30, 40, anchor="w", text="Clean up in one click", font=("Segoe UI", 10, "bold"), fill="#e0f2fe")
        self.hero_canvas.create_text(30, 80, anchor="w", text="Welcome to Technolize", font=("Segoe UI", 22, "bold"), fill="#ffffff")
        self.hero_canvas.create_text(
            30,
            116,
            anchor="w",
            text="Sort documents, media, and everything else safely into folders.",
            font=("Segoe UI", 11),
            fill="#f8fafc",
        )
        hero_btn = self.rounded_button(self.hero_canvas, "View History", self.render_history, fill=ACCENT, hover=ACCENT, fg="#ffffff", bg=ACCENT)
        self.hero_canvas.create_window(30, 154, anchor="w", window=hero_btn)

    def on_resize(self, _event: tk.Event) -> None:
        if self._resize_job:
            self.root.after_cancel(self._resize_job)
        self._resize_job = self.root.after(60, self.draw_hero_content)


def main() -> None:
    log_path = Path(__file__).with_suffix(".runlog")
    try:
        log_path.write_text("start\n")
    except Exception:
        pass
    root = tk.Tk()
    OrganizerApp(root)
    root.mainloop()
    try:
        log_path.write_text(log_path.read_text() + "end\n")
    except Exception:
        pass


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # Log unexpected crashes to console
        import traceback

        traceback.print_exc()
        messagebox.showerror("Unexpected error", str(exc))
