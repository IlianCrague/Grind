"""Shared dark UI theme inspired by VS Code."""

BACKGROUND = "#1e1e1e"
SURFACE = "#252526"
BORDER = "#3c3c3c"
TEXT = "#d4d4d4"
MUTED_TEXT = "#9da3b0"
ACCENT = "#0e639c"
ACCENT_HOVER = "#1177bb"
SUCCESS = "#3fb950"

FONT = "Segoe UI"
TITLE_FONT = (FONT, 22, "bold")
BODY_FONT = (FONT, 12)
VALUE_FONT = (FONT, 16, "bold")


def apply_window_theme(window):
    """Apply the dark background to a root window or frame."""
    window.configure(bg=BACKGROUND)


def frame_style(padding=False):
    style = {
        "bg": SURFACE,
        "highlightbackground": BORDER,
        "highlightthickness": 1,
        "bd": 0,
    }
    if padding:
        style["padx"] = 16
        style["pady"] = 16
    return style


def label_style(size="body"):
    font = BODY_FONT
    fg = TEXT

    if size == "title":
        font = TITLE_FONT
    elif size == "value":
        font = VALUE_FONT
    elif size == "muted":
        fg = MUTED_TEXT

    return {
        "bg": SURFACE,
        "fg": fg,
        "font": font,
    }


def button_style():
    return {
        "font": BODY_FONT,
        "bg": ACCENT,
        "fg": "#ffffff",
        "activebackground": ACCENT_HOVER,
        "activeforeground": "#ffffff",
        "relief": "flat",
        "bd": 0,
        "cursor": "hand2",
        "padx": 14,
        "pady": 8,
        "highlightthickness": 0,
    }


def secondary_button_style():
    style = button_style().copy()
    style.update({"bg": "#3a3d41", "activebackground": "#4c5159"})
    return style


def entry_style():
    return {
        "font": BODY_FONT,
        "bg": "#1f2428",
        "fg": TEXT,
        "insertbackground": TEXT,
        "relief": "flat",
        "bd": 0,
        "highlightbackground": BORDER,
        "highlightcolor": ACCENT,
        "highlightthickness": 1,
    }


def apply_matplotlib_dark(fig, ax):
    """Make a matplotlib figure blend with the dark Tkinter UI."""
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor("#1f1f1f")
    ax.tick_params(colors=MUTED_TEXT)
    for spine in ax.spines.values():
        spine.set_color(BORDER)
    ax.yaxis.label.set_color(TEXT)
    ax.xaxis.label.set_color(TEXT)
    ax.title.set_color(TEXT)
    ax.grid(color="#2d2d30", linestyle="--", linewidth=0.6, alpha=0.5)
