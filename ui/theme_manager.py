"""
Centralized Theme Manager for Light/Dark mode.

Provides:
- THEMES: color palettes
- ThemeManager: manages current mode and notifies observers
- helper functions: get_mode, set_mode, get_palette
"""

from typing import Callable, Dict, Any, List
import tkinter as tk
import ttkbootstrap as ttk


THEMES: Dict[str, Dict[str, str]] = {
    "dark": {
        "bg": "#1e1e1e",
        "workspace_bg": "#1e1e1e",
        "fg": "#ffffff",
        "panel_bg": "#2d2d2d",
        "ai_chat_bg": "#2b2b2b",
        "input_bg": "#2b2b2b",
        "input_fg": "#ffffff",
        "popup_bg": "#1e1e1e",
        "popup_fg": "#ffffff",
        "border": "#3a3a3a",
        "user_text": "#007acc",
        "ai_label": "#28a745",
        "suggest_label": "#17a2b8",
        "old_text": "#ff6b6b",
        "old_bg": "#3a0000",
        "new_text": "#90ee90",
        "new_bg": "#003a00",
        "gen_btn_bg": "#0d6efd",
        "gen_btn_active": "#005a9e",
        "close_btn_bg": "#dc3545",
        "close_btn_active": "#c82333",
        "keep_btn": "#198754",
        "keep_hover": "#27ae60",
        "discard_btn": "#dc3545",
        "discard_hover": "#e74c3c",
        "separator": "#444444",
        "select_bg": "#007acc",
        "select_fg": "#ffffff",
        "history_bg": "#1e1e1e",
        "history_text": "#ffffff",
        "prompt_bg": "#ff8c00",
        "prompt_fg": "#000000",
        "applied_bg": "#2d4a2d",
        "applied_fg": "#90ee90",
    },
    "light": {
        "bg": "#ffffff",
        "workspace_bg": "#ffffff",
        "fg": "#000000",
        "panel_bg": "#ffffff",
        "ai_chat_bg": "#f2f2f2",
        "input_bg": "#f2f2f2",
        "input_fg": "#000000",
        "popup_bg": "#ffffff",
        "popup_fg": "#000000",
        "border": "#dddddd",
        "user_text": "#0d6efd",
        "ai_label": "#198754",
        "suggest_label": "#0dcaf0",
        "old_text": "#c0392b",
        "old_bg": "#ffcccc",
        "new_text": "#2e8b57",
        "new_bg": "#ccffcc",
        "gen_btn_bg": "#0d6efd",
        "gen_btn_active": "#0b5ed7",
        "close_btn_bg": "#dc3545",
        "close_btn_active": "#e74c3c",
        "keep_btn": "#198754",
        "keep_hover": "#28a745",
        "discard_btn": "#dc3545",
        "discard_hover": "#e74c3c",
        "separator": "#888888",
        "select_bg": "#0d6efd",
        "select_fg": "#ffffff",
        "history_bg": "#ffffff",
        "history_text": "#000000",
        "prompt_bg": "#ffecb5",
        "prompt_fg": "#000000",
        "applied_bg": "#ccffcc",
        "applied_fg": "#2e8b57",
    },
}


class ThemeManager:
    def __init__(self, default_mode: str = "dark"):
        self._mode: str = default_mode if default_mode in THEMES else "dark"
        self._observers: List[Callable[[str, Dict[str, str]], None]] = []
        self._theme_lock: bool = False

    def get_mode(self) -> str:
        return self._mode

    def set_mode(self, mode: str) -> None:
        if mode not in THEMES or mode == self._mode:
            self._notify()
            return
        self._mode = mode
        self._apply_ttk_theme()
        self._notify()
        # After observers have updated, apply recursively with one immediate pass and one delayed sweep
        try:
            root = tk._default_root
            if not root:
                return
            # Reset widget-applied flags before pass
            def _reset_theme_flags(widget: Any):
                try:
                    if hasattr(widget, "_theme_applied"):
                        delattr(widget, "_theme_applied")
                    for child in (widget.winfo_children() if hasattr(widget, "winfo_children") else []):
                        _reset_theme_flags(child)
                except Exception:
                    return
            _reset_theme_flags(root)
            self._theme_lock = True
            try:
                for tl in root.winfo_children():
                    try:
                        if isinstance(tl, tk.Toplevel) or isinstance(tl, tk.Tk):
                            self._apply_theme_recursively(tl, self.get_palette())
                    except Exception:
                        continue
                # One delayed sweep for post-layout widgets
                try:
                    root.after_idle(lambda: apply_theme_recursively(root, self.get_palette()))
                except Exception:
                    pass
            finally:
                self._theme_lock = False
        except Exception:
            pass

    def get_palette(self) -> Dict[str, str]:
        return THEMES[self._mode]

    def add_observer(self, callback: Callable[[str, Dict[str, str]], None]) -> None:
        if callback not in self._observers:
            self._observers.append(callback)

    def remove_observer(self, callback: Callable[[str, Dict[str, str]], None]) -> None:
        if callback in self._observers:
            self._observers.remove(callback)

    def _notify(self) -> None:
        pal = self.get_palette()
        for cb in list(self._observers):
            try:
                cb(self._mode, pal)
            except Exception:
                continue

    def _apply_ttk_theme(self) -> None:
        """Apply palette to common ttk styles globally."""
        try:
            style = ttk.Style()
            pal = self.get_palette()
            # Frames and containers
            for s in ["TFrame", "SQL.TFrame", "SideNav.TFrame"]:
                try:
                    style.configure(s, background=pal.get("panel_bg"))
                except Exception:
                    continue
            # Labels
            for s in ["TLabel", "Info.TLabel"]:
                try:
                    style.configure(s, background=pal.get("panel_bg"), foreground=pal.get("fg"))
                except Exception:
                    continue
            # Buttons
            for s in ["TButton", "Accent.TButton"]:
                try:
                    style.configure(s, background=pal.get("gen_btn_bg"), foreground="#ffffff")
                except Exception:
                    continue
            # Notebook/Tabs
            try:
                style.configure("TNotebook", background=pal.get("panel_bg"))
                style.configure("TNotebook.Tab", background=pal.get("panel_bg"), foreground=pal.get("fg"))
            except Exception:
                pass
            # Treeview
            try:
                style.configure("Treeview", background=pal.get("panel_bg"), fieldbackground=pal.get("panel_bg"), foreground=pal.get("fg"))
                style.map("Treeview", background=[("selected", pal.get("select_bg"))], foreground=[("selected", pal.get("select_fg"))])
            except Exception:
                pass
            # Scrollbars best-effort coloring (may be ignored depending on theme)
            try:
                for s in ["Vertical.TScrollbar", "Horizontal.TScrollbar", "TScrollbar"]:
                    style.configure(s, background=pal.get("panel_bg"))
            except Exception:
                pass
        except Exception:
            pass

    def _apply_theme_recursively(self, widget: Any, palette: Dict[str, str]) -> None:
        """Best-effort recursive theming of Tk widget tree."""
        try:
            if not widget or not str(widget):
                return
            # Prevent re-entry for this widget within a single pass
            try:
                if getattr(widget, "_theme_applied", False):
                    return
                widget._theme_applied = True
            except Exception:
                pass
            # Apply based on widget type
            try:
                if isinstance(widget, tk.Canvas):
                    widget.configure(bg=palette.get("workspace_bg", palette.get("bg")))
                elif isinstance(widget, tk.Text):
                    widget.configure(bg=palette.get("workspace_bg", palette.get("bg")),
                                     fg=palette.get("fg"),
                                     insertbackground=palette.get("user_text", palette.get("fg")),
                                     selectbackground=palette.get("select_bg", palette.get("ai_chat_bg")),
                                     selectforeground=palette.get("select_fg", palette.get("fg")))
                elif isinstance(widget, tk.Label):
                    widget.configure(bg=palette.get("panel_bg"), fg=palette.get("fg"))
                elif isinstance(widget, tk.Button):
                    widget.configure(bg=palette.get("panel_bg"), fg=palette.get("fg"), activebackground=palette.get("ai_chat_bg"))
                elif isinstance(widget, tk.PanedWindow):
                    try:
                        widget.configure(bg=palette.get("panel_bg"))
                    except Exception:
                        pass
                elif isinstance(widget, tk.Frame) or isinstance(widget, tk.Toplevel) or isinstance(widget, tk.Tk):
                    widget.configure(bg=palette.get("panel_bg"))
            except Exception:
                pass
            # Recurse children
            try:
                children = widget.winfo_children()
            except Exception:
                children = []
            for child in list(children or []):
                self._apply_theme_recursively(child, palette)
        except Exception:
            pass

def apply_theme_recursively(widget: Any, palette: Dict[str, str] | None = None) -> None:
    try:
        pal = palette or theme_manager.get_palette()
        theme_manager._apply_theme_recursively(widget, pal)
    except Exception:
        pass


# Singleton instance for app-wide use
theme_manager = ThemeManager()


def get_mode() -> str:
    return theme_manager.get_mode()


def set_mode(mode: str) -> None:
    theme_manager.set_mode(mode)


def get_palette() -> Dict[str, str]:
    return theme_manager.get_palette()


