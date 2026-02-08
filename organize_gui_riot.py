"""
Technolize Organizer - Riot Client Inspired Design
Modern, sleek dark UI with neon accents and glass morphism effects.
"""
from __future__ import annotations

import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Tuple
from threading import Thread
import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter as tk

# Set dark theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Riot-Inspired Color Palette
COLORS = {
    "bg_primary": "#0a0e27",      # Very dark blue (main background)
    "bg_secondary": "#0f1428",    # Slightly lighter dark blue
    "bg_card": "#1a2038",         # Card background (glass effect)
    "accent_cyan": "#0dd9ff",     # Neon cyan
    "accent_purple": "#d946ef",   # Neon purple
    "accent_blue": "#3b82f6",     # Electric blue
    "text_primary": "#e0e1ff",    # Light text
    "text_secondary": "#8b92b8",  # Muted text
    "text_muted": "#565d7d",      # Very muted text
    "border": "#252d4a",          # Subtle border
    "success": "#17c655",         # Neon green
    "warning": "#ffa500",         # Orange
}

# Category definition
CATEGORY_MAP: Dict[str, Iterable[str]] = {
    "Documents/Excel": [".xls", ".xlsx", ".xlsm", ".xlsb", ".xltx", ".csv"],
    "Documents/Word": [".doc", ".docx", ".odt", ".rtf"],
    "Documents/PDF": [".pdf"],
    "Documents/Text": [".txt"],
    "Media/Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".heic"],
    "Media/Videos": [".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm", ".m4v"],
}

LEGACY_FOLDER_REMAP: Dict[str, str] = {
    "Excel": "Documents/Excel",
    "Word": "Documents/Word",
    "PDF": "Documents/PDF",
    "Text": "Documents/Text",
}

OTHER_FOLDER = "Other"
HISTORY_FILE = Path.home() / "Documents" / "Technolize" / "organizer_history.json"


def resolve_destination(file_path: Path) -> Path | None:
    ext = file_path.suffix.lower()
    for dest, extensions in CATEGORY_MAP.items():
        if ext in extensions:
            return Path(dest)
    return None


def ensure_unique_path(target: Path) -> Path:
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
    if not target.exists():
        return target
    parent = target.parent
    counter = 1
    while True:
        candidate = parent / f"{target.name} ({counter})"
        if not candidate.exists():
            return candidate
        counter += 1


def preview_organization(base_folder: Path) -> List[Tuple[Path, Path]]:
    moves: List[Tuple[Path, Path]] = []
    for entry in base_folder.iterdir():
        if entry.is_dir():
            continue
        dest_subpath = resolve_destination(entry)
        dest_root = dest_subpath if dest_subpath is not None else Path(OTHER_FOLDER)
        dest_folder = base_folder / dest_root
        target = ensure_unique_path(dest_folder / entry.name)
        moves.append((entry, target))
    return moves


def organize_folder(base_folder: Path) -> List[Tuple[Path, Path]]:
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
        try:
            src_dir.rmdir()
        except OSError:
            pass


class RiotFileOrganizer:
    def __init__(self, root: ctk.CTk) -> None:
        self.root = root
        self.root.title("Technolize Organizer")
        self.root.geometry("1600x900")
        
        # Set window icon
        try:
            icon_path = Path(__file__).parent / "assets" / "logo.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except Exception as e:
            print(f"Could not load icon: {e}")
        
        # Center window
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 1600) // 2
        y = (screen_height - 900) // 2
        self.root.geometry(f"1600x900+{x}+{y}")
        self.root.minsize(1200, 700)

        # Configure root appearance
        self.root.configure(fg_color=COLORS["bg_primary"])

        self.folder_var = tk.StringVar(value=str(self.default_downloads()))
        self.history: list[dict] = []
        self.history_file = HISTORY_FILE
        self.is_organizing = False
        self.current_tab = "home"

        self.load_history()
        self.apply_custom_styles()
        self.build_ui()

    def default_downloads(self) -> Path:
        downloads = Path.home() / "Downloads"
        return downloads if downloads.exists() else Path.home()

    def apply_custom_styles(self) -> None:
        """Apply custom styling for Riot-like appearance"""
        self.style = ctk.CTkFont(family="Segoe UI", size=13)
        self.style_small = ctk.CTkFont(family="Segoe UI", size=12)
        self.style_title = ctk.CTkFont(family="Segoe UI", size=32, weight="bold")
        self.style_heading = ctk.CTkFont(family="Segoe UI", size=18, weight="bold")
        self.style_label = ctk.CTkFont(family="Segoe UI", size=12)

    def build_ui(self) -> None:
        """Build main UI with Riot client aesthetic"""
        # Root container
        main_container = ctk.CTkFrame(self.root, fg_color=COLORS["bg_primary"])
        main_container.pack(fill="both", expand=True)

        # Sidebar
        sidebar = ctk.CTkFrame(main_container, fg_color=COLORS["bg_secondary"], width=200)
        sidebar.pack(side="left", fill="y", padx=0, pady=0)
        sidebar.pack_propagate(False)

        # Logo/Brand
        brand = ctk.CTkLabel(
            sidebar,
            text="TECHNOLIZE",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=COLORS["accent_cyan"],
        )
        brand.pack(padx=20, pady=20, anchor="w")

        # Divider
        divider = ctk.CTkFrame(sidebar, fg_color=COLORS["border"], height=1)
        divider.pack(fill="x", padx=10, pady=(0, 20))

        # Navigation items
        self.nav_buttons = {}
        nav_items = [
            ("HOME", "home", "🏠"),
            ("ORGANIZE", "organize", "⚡"),
            ("PREVIEW", "preview", "👁"),
            ("HISTORY", "history", "📜"),
            ("STATS", "stats", "📊"),
        ]

        for label, tab_id, icon in nav_items:
            self.add_nav_button(sidebar, label, tab_id, icon)

        # Bottom spacer
        ctk.CTkFrame(sidebar, fg_color=COLORS["bg_secondary"]).pack(fill="both", expand=True)

        # Settings button at bottom
        settings_btn = ctk.CTkButton(
            sidebar,
            text="⚙️ SETTINGS",
            text_color=COLORS["text_secondary"],
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="transparent",
            hover_color=COLORS["bg_card"],
            command=lambda: self.switch_tab("settings"),
        )
        settings_btn.pack(fill="x", padx=15, pady=10)

        # Main content area
        self.content_area = ctk.CTkFrame(main_container, fg_color=COLORS["bg_primary"])
        self.content_area.pack(side="right", fill="both", expand=True, padx=30, pady=30)

        # Set default view
        self.switch_tab("home")

    def add_nav_button(self, parent, label: str, tab_id: str, icon: str) -> None:
        btn = ctk.CTkButton(
            parent,
            text=f"{icon} {label}",
            text_color=COLORS["text_secondary"],
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            fg_color="transparent",
            hover_color=COLORS["bg_card"],
            command=lambda: self.switch_tab(tab_id),
        )
        btn.pack(fill="x", padx=15, pady=8)
        self.nav_buttons[tab_id] = btn

    def switch_tab(self, tab_id: str) -> None:
        """Switch to a different tab"""
        self.current_tab = tab_id

        # Update nav colors
        for tid, btn in self.nav_buttons.items():
            if tid == tab_id:
                btn.configure(
                    text_color=COLORS["accent_cyan"],
                    fg_color=COLORS["bg_card"],
                )
            else:
                btn.configure(
                    text_color=COLORS["text_secondary"],
                    fg_color="transparent",
                )

        # Clear content
        for widget in self.content_area.winfo_children():
            widget.destroy()

        # Load tab
        if tab_id == "home":
            self.show_home()
        elif tab_id == "organize":
            self.show_organize()
        elif tab_id == "preview":
            self.show_preview()
        elif tab_id == "history":
            self.show_history()
        elif tab_id == "stats":
            self.show_stats()
        elif tab_id == "settings":
            self.show_settings()

    def show_home(self) -> None:
        """Home/Dashboard tab"""
        # Header
        header = ctk.CTkLabel(
            self.content_area,
            text="TECHNOLIZE ORGANIZER",
            font=self.style_title,
            text_color=COLORS["accent_cyan"],
        )
        header.pack(anchor="w", pady=(0, 10))

        subtitle = ctk.CTkLabel(
            self.content_area,
            text="Organize your files effortlessly",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=COLORS["text_secondary"],
        )
        subtitle.pack(anchor="w", pady=(0, 30))

        # Stats cards row
        stats_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 30))

        last_run = self.history[0] if self.history else None
        stats = [
            ("RUNS", len(self.history)),
            ("FILES MOVED", sum(len(h["moves"]) for h in self.history)),
            ("LAST RUN", last_run["label"].split("•")[0].strip() if last_run else "NEVER"),
        ]

        for i, (label, value) in enumerate(stats):
            self.create_stat_card(stats_frame, label, str(value), i, font_size=18)

        # Quick action buttons - REMOVED (use sidebar navigation instead)
        # Users can click HOME, ORGANIZE, PREVIEW tabs directly in sidebar

        # Info section
        info_frame = self.create_glass_card(self.content_area)
        info_frame.pack(fill="both", expand=True, pady=(0, 10))

        info_title = ctk.CTkLabel(
            info_frame,
            text="HOW IT WORKS",
            font=self.style_heading,
            text_color=COLORS["accent_cyan"],
        )
        info_title.pack(anchor="w", padx=20, pady=(20, 15))

        steps = [
            ("1", "Select your folder", COLORS["accent_purple"]),
            ("2", "Preview the changes", COLORS["accent_blue"]),
            ("3", "Execute the organization", COLORS["accent_cyan"]),
            ("4", "Check your results", COLORS["success"]),
        ]

        for num, text, color in steps:
            step_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
            step_frame.pack(fill="x", padx=20, pady=8)

            num_label = ctk.CTkLabel(
                step_frame,
                text=num,
                font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                text_color=color,
                width=30,
            )
            num_label.pack(side="left", anchor="w")

            text_label = ctk.CTkLabel(
                step_frame,
                text=text,
                font=ctk.CTkFont(family="Segoe UI", size=13),
                text_color=COLORS["text_secondary"],
            )
            text_label.pack(side="left", anchor="w")

        ctk.CTkLabel(info_frame, text="").pack(pady=10)

    def show_organize(self) -> None:
        """Organize tab"""
        # Header
        header = ctk.CTkLabel(
            self.content_area,
            text="ORGANIZE",
            font=self.style_title,
            text_color=COLORS["accent_cyan"],
        )
        header.pack(anchor="w", pady=(0, 20))

        # Folder selection card
        select_card = self.create_glass_card(self.content_area)
        select_card.pack(fill="x", pady=(0, 20))

        select_title = ctk.CTkLabel(
            select_card,
            text="SELECT FOLDER",
            font=self.style_heading,
            text_color=COLORS["accent_cyan"],
        )
        select_title.pack(anchor="w", padx=20, pady=(20, 15))

        # Input container
        input_frame = ctk.CTkFrame(select_card, fg_color=COLORS["bg_primary"], corner_radius=6)
        input_frame.pack(fill="x", padx=20, pady=(0, 20))

        self.folder_entry = ctk.CTkEntry(
            input_frame,
            textvariable=self.folder_var,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS["text_primary"],
            fg_color=COLORS["bg_primary"],
            border_color=COLORS["border"],
            border_width=1,
            height=40,
        )
        self.folder_entry.pack(side="left", fill="both", expand=True, padx=(10, 5), pady=8)

        browse_btn = ctk.CTkButton(
            input_frame,
            text="BROWSE",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=COLORS["accent_purple"],
            hover_color=COLORS["accent_cyan"],
            text_color=COLORS["bg_primary"],
            width=100,
            command=self.choose_folder,
        )
        browse_btn.pack(side="left", padx=5, pady=8)

        # Categories info
        cat_card = self.create_glass_card(self.content_area)
        cat_card.pack(fill="both", expand=True, pady=(0, 20))

        cat_title = ctk.CTkLabel(
            cat_card,
            text="CATEGORIES",
            font=self.style_heading,
            text_color=COLORS["accent_cyan"],
        )
        cat_title.pack(anchor="w", padx=20, pady=(20, 15))

        categories = [
            ("DOCUMENTS", "Excel, Word, PDF, Text", COLORS["accent_blue"]),
            ("MEDIA", "Images, Videos", COLORS["accent_purple"]),
            ("OTHER", "Uncategorized files", COLORS["accent_cyan"]),
        ]

        for cat_name, desc, color in categories:
            cat_frame = ctk.CTkFrame(cat_card, fg_color="transparent")
            cat_frame.pack(fill="x", padx=20, pady=10)

            name = ctk.CTkLabel(
                cat_frame,
                text=cat_name,
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                text_color=color,
            )
            name.pack(anchor="w")

            desc_label = ctk.CTkLabel(
                cat_frame,
                text=desc,
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color=COLORS["text_secondary"],
            )
            desc_label.pack(anchor="w", pady=(2, 0))

        ctk.CTkLabel(cat_card, text="").pack(pady=5)

        # Action buttons
        btn_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        btn_frame.pack(fill="x")

        self.create_accent_button(btn_frame, "PREVIEW FIRST", self.show_preview).pack(
            side="left", fill="both", expand=True, padx=(0, 10)
        )
        self.create_accent_button(btn_frame, "EXECUTE", self.on_organize, accent=True).pack(
            side="left", fill="both", expand=True
        )

    def show_preview(self) -> None:
        """Preview tab"""
        header = ctk.CTkLabel(
            self.content_area,
            text="PREVIEW",
            font=self.style_title,
            text_color=COLORS["accent_cyan"],
        )
        header.pack(anchor="w", pady=(0, 20))

        folder = Path(self.folder_var.get()).expanduser()

        if not folder.exists():
            error_card = self.create_glass_card(self.content_area)
            error_card.pack(fill="both", expand=True)

            error_label = ctk.CTkLabel(
                error_card,
                text="SELECT A VALID FOLDER FIRST",
                font=self.style_heading,
                text_color=COLORS["warning"],
            )
            error_label.pack(pady=40)
            return

        moves = preview_organization(folder)

        preview_card = self.create_glass_card(self.content_area)
        preview_card.pack(fill="both", expand=True, pady=(0, 20))

        # Count
        count_label = ctk.CTkLabel(
            preview_card,
            text=f"{len(moves)} FILES WILL BE ORGANIZED",
            font=self.style_heading,
            text_color=COLORS["accent_cyan"],
        )
        count_label.pack(anchor="w", padx=20, pady=(20, 15))

        # Preview text
        preview_text = ctk.CTkTextbox(
            preview_card,
            font=ctk.CTkFont(family="Courier", size=13),
            text_color=COLORS["text_secondary"],
            fg_color=COLORS["bg_primary"],
            border_color=COLORS["border"],
            border_width=1,
        )
        preview_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        for i, (src, dest) in enumerate(moves, 1):
            rel_dest = dest.relative_to(folder)
            preview_text.insert("end", f"{i:3d}. {src.name}\n     → {rel_dest}\n\n")

        preview_text.configure(state="disabled")

        # Action buttons
        btn_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        btn_frame.pack(fill="x")

        self.create_accent_button(btn_frame, "PROCEED", self.on_organize, accent=True).pack(
            side="left", fill="both", expand=True, padx=(0, 10)
        )
        self.create_accent_button(btn_frame, "BACK", self.show_organize, accent=False).pack(
            side="left", fill="both", expand=True
        )

    def show_history(self) -> None:
        """History tab"""
        header = ctk.CTkLabel(
            self.content_area,
            text="HISTORY",
            font=self.style_title,
            text_color=COLORS["accent_cyan"],
        )
        header.pack(anchor="w", pady=(0, 20))

        if not self.history:
            empty_card = self.create_glass_card(self.content_area)
            empty_card.pack(fill="both", expand=True)

            empty_label = ctk.CTkLabel(
                empty_card,
                text="NO ORGANIZATION RUNS YET",
                font=self.style_label,
                text_color=COLORS["text_secondary"],
            )
            empty_label.pack(pady=40)
            return

        # Create scrollable frame for history entries
        scroll_frame = ctk.CTkScrollableFrame(
            self.content_area,
            fg_color=COLORS["bg_primary"],
            label_text="",
        )
        scroll_frame.pack(fill="both", expand=True, pady=(0, 20))

        # Create expandable history entries
        for idx, run in enumerate(self.history):
            try:
                print(f"[DEBUG] Creating entry {idx}: {run.get('label', 'N/A')}")
                self.create_history_entry(scroll_frame, run, idx)
            except Exception as e:
                print(f"[ERROR] Failed to create history entry {idx}: {e}")
                import traceback
                traceback.print_exc()

        # Clear button
        clear_btn = ctk.CTkButton(
            self.content_area,
            text="CLEAR HISTORY",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=COLORS["accent_purple"],
            text_color=COLORS["bg_primary"],
            command=self.clear_history,
        )
        clear_btn.pack(fill="x")

    def create_history_entry(self, parent, run: dict, index: int) -> None:
        """Create an expandable history entry"""
        container = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=8)
        container.pack(fill="x", pady=5, padx=0)

        # Store expanded state
        is_expanded = tk.BooleanVar(value=False)
        details_frame_container = [None]  # Use list to hold mutable reference
        
        # Header frame
        header_frame = ctk.CTkFrame(container, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=10)

        # Arrow label
        arrow_label = ctk.CTkLabel(
            header_frame,
            text="▶",
            font=ctk.CTkFont(family="Segoe UI", size=16),
            text_color=COLORS["accent_cyan"],
            width=20,
        )
        arrow_label.pack(side="left", padx=(0, 10))

        # Info section
        info_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)

        title_label = ctk.CTkLabel(
            info_frame,
            text=run['label'],
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=COLORS["text_primary"],
            anchor="w",
        )
        title_label.pack(anchor="w")

        files_label = ctk.CTkLabel(
            info_frame,
            text=f"📊 {len(run['moves'])} files",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["text_secondary"],
            anchor="w",
        )
        files_label.pack(anchor="w")

        # Define toggle function after arrow_label is created
        def toggle_expand():
            details_frame = details_frame_container[0]
            if is_expanded.get():
                # Collapse
                if details_frame:
                    details_frame.destroy()
                    details_frame_container[0] = None
                is_expanded.set(False)
                arrow_label.configure(text="▶")
            else:
                # Expand
                is_expanded.set(True)
                arrow_label.configure(text="▼")
                
                # Create details frame
                details_frame = ctk.CTkFrame(container, fg_color=COLORS["bg_primary"], corner_radius=5)
                details_frame.pack(fill="x", padx=10, pady=(5, 10))
                details_frame_container[0] = details_frame

                if len(run['moves']) == 0:
                    no_files = ctk.CTkLabel(
                        details_frame,
                        text="   No files were moved",
                        font=ctk.CTkFont(family="Segoe UI", size=13),
                        text_color=COLORS["text_muted"],
                    )
                    no_files.pack(anchor="w", padx=10, pady=10)
                else:
                    for src, dest in run['moves']:
                        try:
                            rel_dest = dest.relative_to(run['base'])
                            file_label = ctk.CTkLabel(
                                details_frame,
                                text=f"   • {src.name} → {rel_dest}",
                                font=ctk.CTkFont(family="Courier", size=13),
                                text_color=COLORS["text_secondary"],
                                anchor="w",
                            )
                            file_label.pack(fill="x", padx=10, pady=2)
                        except:
                            file_label = ctk.CTkLabel(
                                details_frame,
                                text=f"   • {src.name} → {dest}",
                                font=ctk.CTkFont(family="Courier", size=13),
                                text_color=COLORS["text_secondary"],
                                anchor="w",
                            )
                            file_label.pack(fill="x", padx=10, pady=2)

        # Make header clickable
        header_frame.bind("<Button-1>", lambda e: toggle_expand())
        arrow_label.bind("<Button-1>", lambda e: toggle_expand())
        title_label.bind("<Button-1>", lambda e: toggle_expand())
        files_label.bind("<Button-1>", lambda e: toggle_expand())

    def show_stats(self) -> None:
        """Statistics tab"""
        header = ctk.CTkLabel(
            self.content_area,
            text="STATISTICS",
            font=self.style_title,
            text_color=COLORS["accent_cyan"],
        )
        header.pack(anchor="w", pady=(0, 20))

        total_runs = len(self.history)
        total_files = sum(len(h["moves"]) for h in self.history)

        category_counts = {}
        for run in self.history:
            for src, dest in run["moves"]:
                dest_str = str(dest)
                category = dest_str.split("\\")[0] if "\\" in dest_str else dest_str
                category_counts[category] = category_counts.get(category, 0) + 1

        # Stats cards
        stats_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 30))

        stats = [
            ("TOTAL RUNS", total_runs, COLORS["accent_cyan"]),
            ("FILES MOVED", total_files, COLORS["accent_purple"]),
            ("CATEGORIES", len(category_counts), COLORS["accent_blue"]),
        ]

        for i, (label, value, color) in enumerate(stats):
            self.create_stat_card(stats_frame, label, str(value), i, color, font_size=18)

        # Category breakdown
        if category_counts:
            cat_card = self.create_glass_card(self.content_area)
            cat_card.pack(fill="both", expand=True)

            cat_title = ctk.CTkLabel(
                cat_card,
                text="CATEGORY BREAKDOWN",
                font=self.style_heading,
                text_color=COLORS["accent_cyan"],
            )
            cat_title.pack(anchor="w", padx=20, pady=(20, 15))

            for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
                cat_frame = ctk.CTkFrame(cat_card, fg_color="transparent")
                cat_frame.pack(fill="x", padx=20, pady=10)

                cat_label = ctk.CTkLabel(
                    cat_frame,
                    text=f"{category.upper()}: {count} FILES",
                    font=ctk.CTkFont(family="Segoe UI", size=12),
                    text_color=COLORS["text_secondary"],
                )
                cat_label.pack(anchor="w")

                # Progress bar simulation
                bar_frame = ctk.CTkFrame(cat_frame, fg_color=COLORS["bg_primary"], height=4)
                bar_frame.pack(fill="x", pady=(5, 0))

                bar_fill = ctk.CTkFrame(
                    bar_frame,
                    fg_color=COLORS["accent_cyan"],
                    height=4,
                )
                width_percent = min(count / max(category_counts.values()) * 100, 100)
                bar_fill.place(relwidth=width_percent / 100)

            ctk.CTkLabel(cat_card, text="").pack(pady=10)

    def show_settings(self) -> None:
        """Settings tab"""
        header = ctk.CTkLabel(
            self.content_area,
            text="SETTINGS",
            font=self.style_title,
            text_color=COLORS["accent_cyan"],
        )
        header.pack(anchor="w", pady=(0, 20))

        settings_card = self.create_glass_card(self.content_area)
        settings_card.pack(fill="both", expand=True)

        settings_title = ctk.CTkLabel(
            settings_card,
            text="APPLICATION",
            font=self.style_heading,
            text_color=COLORS["accent_cyan"],
        )
        settings_title.pack(anchor="w", padx=20, pady=(20, 15))

        # Settings items
        settings = [
            ("Version", "2.0 - Riot Edition"),
            ("Status", "Production Ready"),
            ("Theme", "Dark - Neon Accents"),
            ("History", f"{len(self.history)} runs saved"),
        ]

        for setting_name, setting_value in settings:
            setting_frame = ctk.CTkFrame(settings_card, fg_color="transparent")
            setting_frame.pack(fill="x", padx=20, pady=10)

            name = ctk.CTkLabel(
                setting_frame,
                text=setting_name,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color=COLORS["accent_cyan"],
                width=100,
            )
            name.pack(side="left", anchor="w")

            value = ctk.CTkLabel(
                setting_frame,
                text=setting_value,
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color=COLORS["text_secondary"],
            )
            value.pack(side="left", anchor="w")

        ctk.CTkLabel(settings_card, text="").pack(pady=10)

    def create_glass_card(self, parent) -> ctk.CTkFrame:
        """Create a glass-morphism card"""
        return ctk.CTkFrame(
            parent,
            fg_color=COLORS["bg_card"],
            border_color=COLORS["border"],
            border_width=1,
            corner_radius=8,
        )

    def create_stat_card(self, parent, label: str, value: str, index: int, color: str = None, font_size: int = 14) -> None:
        """Create a stat card"""
        if color is None:
            colors = [COLORS["accent_cyan"], COLORS["accent_purple"], COLORS["accent_blue"]]
            color = colors[index % len(colors)]

        card = self.create_glass_card(parent)
        card.grid(row=0, column=index, sticky="nsew", padx=(0, 15))
        parent.grid_columnconfigure(index, weight=1)

        label_widget = ctk.CTkLabel(
            card,
            text=label,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=COLORS["text_secondary"],
        )
        label_widget.pack(anchor="w", padx=15, pady=(15, 8))

        value_widget = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(family="Segoe UI", size=font_size + 8, weight="bold"),
            text_color=color,
        )
        value_widget.pack(anchor="w", padx=15, pady=(0, 15))

    def create_accent_button(self, parent, text: str, command, accent: bool = True, size: int = 11):
        """Create an accent button"""
        if accent:
            return ctk.CTkButton(
                parent,
                text=text,
                font=ctk.CTkFont(family="Segoe UI", size=size, weight="bold"),
                fg_color=COLORS["accent_cyan"],
                hover_color=COLORS["accent_purple"],
                text_color=COLORS["bg_primary"],
                height=45,
                command=command,
            )
        else:
            return ctk.CTkButton(
                parent,
                text=text,
                font=ctk.CTkFont(family="Segoe UI", size=size, weight="bold"),
                fg_color=COLORS["bg_card"],
                border_color=COLORS["border"],
                border_width=1,
                text_color=COLORS["accent_cyan"],
                hover_color=COLORS["bg_secondary"],
                height=45,
                command=command,
            )

    def choose_folder(self) -> None:
        selected = filedialog.askdirectory(title="Select folder to organize")
        if selected:
            self.folder_var.set(selected)

    def on_organize(self) -> None:
        folder = Path(self.folder_var.get()).expanduser()

        if not folder.exists() or not folder.is_dir():
            messagebox.showerror("Error", "Please select a valid folder")
            return

        if self.is_organizing:
            messagebox.showwarning("Busy", "Organization in progress...")
            return

        self.is_organizing = True

        def organize_thread():
            try:
                moves = organize_folder(folder)
                self.add_history(folder, moves)
                self.root.after(0, lambda: self.show_success(len(moves)))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.is_organizing = False

        Thread(target=organize_thread, daemon=True).start()

    def show_success(self, count: int) -> None:
        messagebox.showinfo("Success", f"✨ {count} files organized!")
        self.switch_tab("history")

    def add_history(self, base: Path, moves: List[Tuple[Path, Path]]) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "label": f"{timestamp} • {base}",
            "moves": moves,
            "base": base,
        }
        print(f"[DEBUG] Adding history entry with {len(moves)} moves")
        self.history.insert(0, entry)
        if len(self.history) > 50:
            self.history = self.history[:50]
        print(f"[DEBUG] Total history entries: {len(self.history)}")
        self.save_history()

    def clear_history(self) -> None:
        if messagebox.askyesno("Confirm", "Clear all history?"):
            self.history = []
            self.save_history()
            self.show_history()

    def save_history(self) -> None:
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            serializable = []
            for run in self.history:
                serializable.append({
                    "label": run.get("label", ""),
                    "base": str(run.get("base", "")),
                    "moves": [{"src": str(src), "dest": str(dest)} for src, dest in run.get("moves", [])],
                })
            with self.history_file.open("w", encoding="utf-8") as fh:
                json.dump(serializable, fh, indent=2)
        except Exception:
            pass

    def load_history(self) -> None:
        if not self.history_file.exists():
            self.history = []
            return
        try:
            data = json.loads(self.history_file.read_text(encoding="utf-8"))
            raw_runs = data if isinstance(data, list) else data.get("history", [])
            loaded = []
            for run in raw_runs:
                base = Path(run.get("base", "")) if run.get("base") else Path.home()
                moves_list = []
                for mv in run.get("moves", []):
                    try:
                        moves_list.append((Path(mv.get("src", "")), Path(mv.get("dest", ""))))
                    except Exception:
                        continue
                loaded.append({"label": run.get("label", ""), "base": base, "moves": moves_list})
            self.history = loaded[:50]
        except Exception:
            self.history = []


def main() -> None:
    root = ctk.CTk()
    RiotFileOrganizer(root)
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        import traceback
        traceback.print_exc()
        messagebox.showerror("Error", f"Application error: {exc}")
