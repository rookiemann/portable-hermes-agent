"""
Hermes Agent - Theme System
Matching ImageBuddy/ImageDownloader visual style.
Pure tkinter + ttk, no external UI libraries.
"""
import ctypes
import tkinter as tk
from tkinter import ttk


# ============================================================================
# Color Palettes
# ============================================================================

DARK = {
    # Backgrounds
    "bg_main": "#1e1e1e",
    "bg_card": "#2d2d2d",
    "bg_sidebar": "#252525",
    "bg_input": "#3c3c3c",
    "bg_hover": "#383838",
    "bg_selected": "#404040",

    # Text
    "text_primary": "#e0e0e0",
    "text_secondary": "#b0b0b0",
    "text_hint": "#a0a0a0",
    "text_disabled": "#707070",

    # Accent
    "accent": "#3b9eff",
    "accent_dark": "#2d7fd4",
    "accent_light": "#1a3a52",

    # Status
    "success": "#81C784",
    "success_dark": "#66BB6A",
    "warning": "#FFCC80",
    "warning_dark": "#FFB74D",
    "danger": "#FF8A80",
    "danger_dark": "#FF6B6B",
    "info": "#42A5F5",

    # Borders
    "border": "#444444",
    "border_light": "#3a3a3a",
    "border_dark": "#555555",
    "separator": "#404040",

    # Scrollbar
    "scrollbar_bg": "#2a2a2a",
    "scrollbar_fg": "#555555",

    # Misc
    "treeview_alt": "#262626",
    "tooltip_bg": "#e0e0e0",
    "tooltip_fg": "#1e1e1e",

    # Message bubbles (Hermes-specific)
    "msg_user": "#1a3a52",
    "msg_user_border": "#2d7fd4",
    "msg_ai": "#1e2e1e",
    "msg_ai_border": "#3a6a3a",
    "msg_tool": "#2e2a1a",
    "msg_tool_border": "#5a4a2a",
    "msg_system": "#2a2a2a",
    "msg_system_border": "#444444",
    "msg_error": "#3a1a1a",
    "msg_error_border": "#FF6B6B",
}

# Fonts
FONTS = {
    "heading": ("Segoe UI", 13, "bold"),
    "subheading": ("Segoe UI", 11, "bold"),
    "body": ("Segoe UI", 10),
    "small": ("Segoe UI", 9),
    "mono": ("Consolas", 10),
    "mono_small": ("Consolas", 9),
    "button": ("Segoe UI", 10, "bold"),
    "title": ("Segoe UI", 16, "bold"),
    "logo": ("Segoe UI", 24, "bold"),
    "logo_sub": ("Segoe UI", 14),
}

# Active color set
C = DARK


def get_color(key: str) -> str:
    return C.get(key, "#ff00ff")


# ============================================================================
# Dark Title Bar (Windows 10/11)
# ============================================================================

def set_dark_title_bar(window):
    """Enable dark title bar on Windows 10/11 via DwmSetWindowAttribute."""
    try:
        window.update()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        value = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 20, ctypes.byref(value), ctypes.sizeof(value)
        )
    except Exception:
        pass


def center_window(window, width=None, height=None, parent=None):
    """Center a window on screen or over its parent window.

    If *parent* is given (and visible), the window is centered over the parent.
    Otherwise it is centered on the primary monitor.
    """
    window.update_idletasks()
    w = width or window.winfo_width()
    h = height or window.winfo_height()

    if parent is not None:
        # Center over parent
        try:
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            x = px + (pw - w) // 2
            y = py + (ph - h) // 2
        except Exception:
            # Fallback to screen center
            x = (window.winfo_screenwidth() - w) // 2
            y = (window.winfo_screenheight() - h) // 2
    else:
        x = (window.winfo_screenwidth() - w) // 2
        y = (window.winfo_screenheight() - h) // 2

    # Clamp to screen bounds
    x = max(0, x)
    y = max(0, y)

    window.geometry(f"{w}x{h}+{x}+{y}")


# ============================================================================
# TTK Style Configuration
# ============================================================================

def apply_theme(root: tk.Tk):
    """Apply the full theme to the root window and all ttk styles."""
    style = ttk.Style()
    style.theme_use("classic")

    bg = C["bg_main"]
    card = C["bg_card"]
    sidebar = C["bg_sidebar"]
    inp = C["bg_input"]
    hover = C["bg_hover"]
    txt = C["text_primary"]
    txt2 = C["text_secondary"]
    hint = C["text_hint"]
    dis = C["text_disabled"]
    accent = C["accent"]
    accent_dk = C["accent_dark"]
    danger = C["danger"]
    danger_dk = C["danger_dark"]
    sep = C["separator"]
    sb_bg = C["scrollbar_bg"]
    sb_fg = C["scrollbar_fg"]
    bd_dk = C["border_dark"]

    # ---- Frames ----
    style.configure("TFrame", background=bg)
    style.configure("Main.TFrame", background=bg)
    style.configure("Sidebar.TFrame", background=sidebar)
    style.configure("Card.TFrame", background=card)

    # ---- Labels ----
    style.configure("TLabel", background=bg, foreground=txt, font=FONTS["body"])
    style.configure("Heading.TLabel", font=FONTS["heading"], foreground=txt, background=bg)
    style.configure("Subheading.TLabel", font=FONTS["subheading"], foreground=txt, background=bg)
    style.configure("Hint.TLabel", font=FONTS["small"], foreground=hint, background=bg)
    style.configure("Accent.TLabel", foreground=accent, background=bg, font=FONTS["body"])
    style.configure("Sidebar.TLabel", background=sidebar, foreground=txt, font=FONTS["body"])

    # ---- Buttons ----
    style.configure("TButton", font=FONTS["body"], padding=6,
                    background=sidebar, foreground=txt)
    style.map("TButton",
              background=[("active", hover), ("pressed", hover)],
              foreground=[("disabled", dis)])

    style.configure("Primary.TButton", foreground="white", background=accent,
                    font=FONTS["button"])
    style.map("Primary.TButton",
              background=[("active", accent_dk), ("pressed", accent_dk)],
              foreground=[("disabled", dis)])

    style.configure("Danger.TButton", foreground="white", background=danger,
                    font=FONTS["button"])
    style.map("Danger.TButton",
              background=[("active", danger_dk), ("pressed", danger_dk)],
              foreground=[("disabled", dis)])

    style.configure("Small.TButton", font=FONTS["small"], padding=[6, 3],
                    background=sidebar, foreground=txt)
    style.map("Small.TButton",
              background=[("active", hover), ("pressed", hover)],
              foreground=[("disabled", dis)])

    style.configure("Small.Primary.TButton", font=FONTS["small"], padding=[6, 3],
                    foreground="white", background=accent)
    style.map("Small.Primary.TButton",
              background=[("active", accent_dk), ("pressed", accent_dk)],
              foreground=[("disabled", dis)])

    # ---- Notebook (Tabs) ----
    style.configure("TNotebook", background=bg, borderwidth=0)
    style.configure("TNotebook.Tab", padding=[20, 10], font=FONTS["subheading"],
                    background=sidebar, foreground=txt2)
    style.map("TNotebook.Tab",
              background=[("selected", card), ("active", hover)],
              foreground=[("selected", accent), ("!selected", txt)])

    # ---- Entry ----
    style.configure("TEntry", fieldbackground=inp, foreground=txt, insertcolor=txt)

    # ---- Combobox ----
    style.configure("TCombobox", font=FONTS["body"], padding=4,
                    fieldbackground=inp, foreground=txt,
                    background=inp, arrowcolor=txt)
    style.map("TCombobox",
              fieldbackground=[("readonly", inp), ("disabled", sidebar)],
              foreground=[("readonly", txt), ("disabled", dis)],
              background=[("readonly", inp)])

    root.option_add("*TCombobox*Listbox.background", inp)
    root.option_add("*TCombobox*Listbox.foreground", txt)
    root.option_add("*TCombobox*Listbox.selectBackground", accent)
    root.option_add("*TCombobox*Listbox.selectForeground", "white")

    # ---- Text ----
    root.option_add("*Text.background", inp)
    root.option_add("*Text.foreground", txt)
    root.option_add("*Text.insertBackground", txt)
    root.option_add("*Text.selectBackground", accent)
    root.option_add("*Text.selectForeground", "white")

    # ---- Scrollbar ----
    root.option_add("*Scrollbar.background", sb_fg)
    root.option_add("*Scrollbar.troughColor", sb_bg)
    root.option_add("*Scrollbar.activeBackground", bd_dk)
    root.option_add("*Scrollbar.highlightBackground", bg)
    root.option_add("*Scrollbar.highlightColor", bg)

    style.configure("TScrollbar", background=sb_fg, troughcolor=sb_bg)

    # ---- Checkbutton ----
    style.configure("TCheckbutton", background=bg, foreground=txt)
    style.map("TCheckbutton", foreground=[("disabled", dis)],
              background=[("disabled", bg)])

    # ---- Progressbar ----
    style.configure("TProgressbar", background=accent, troughcolor=sb_bg)
    style.configure("Green.Horizontal.TProgressbar", background=C["success"], troughcolor=sb_bg)
    style.configure("Orange.Horizontal.TProgressbar", background=C["warning_dark"], troughcolor=sb_bg)
    style.configure("Red.Horizontal.TProgressbar", background=C["danger"], troughcolor=sb_bg)

    # ---- Separator ----
    style.configure("TSeparator", background=sep)

    # ---- Labelframe ----
    style.configure("TLabelframe", background=bg, foreground=txt)
    style.configure("TLabelframe.Label", background=bg, foreground=txt, font=FONTS["subheading"])

    # ---- Context menu colors ----
    root.option_add("*Menu.background", "#2a2a2a")
    root.option_add("*Menu.foreground", "#ffffff")
    root.option_add("*Menu.activeBackground", "#404040")
    root.option_add("*Menu.activeForeground", "#ffffff")

    # Set window background
    root.configure(bg=bg)

    # Dark title bar
    set_dark_title_bar(root)


# ============================================================================
# Tooltip Utility
# ============================================================================

class Tooltip:
    """Hover tooltip for any widget."""

    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tip_window = None
        self._after_id = None
        widget.bind("<Enter>", self._schedule)
        widget.bind("<Leave>", self._hide)

    def _schedule(self, event):
        self._after_id = self.widget.after(self.delay, self._show)

    def _show(self):
        if self.tip_window:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text,
                        background=C["tooltip_bg"], foreground=C["tooltip_fg"],
                        font=FONTS["small"], padx=8, pady=4, relief="solid", borderwidth=1)
        label.pack()

    def _hide(self, event=None):
        if self._after_id:
            self.widget.after_cancel(self._after_id)
            self._after_id = None
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None
