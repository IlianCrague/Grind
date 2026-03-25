import tkinter as tk
import os
from grind_feature import create_window
from simple_display import create_window_simple_display
from max import create_window_max
from ui_theme import (
    apply_window_theme,
    frame_style,
    label_style,
    button_style,
    secondary_button_style,
)


def create_menu_window():
    """Display menu and run each feature inside the same window."""
    root = tk.Tk()
    root.title("Grind")
    root.geometry("800x600")
    apply_window_theme(root)

    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)

    menu_frame = tk.Frame(root, bg="#1e1e1e")
    feature_frame = tk.Frame(root, bg="#1e1e1e")

    for frame in (menu_frame, feature_frame):
        frame.grid(row=0, column=0, sticky="nsew")

    menu_card = tk.Frame(menu_frame, **frame_style())
    menu_card.pack(padx=24, pady=24, fill="both", expand=True)

    title = tk.Label(menu_card, text="Grind", **label_style("title"))
    title.pack(pady=(24, 8))

    feature_cleanup = None

    def show_menu():
        menu_frame.tkraise()

    def open_feature(filename):
        nonlocal feature_cleanup
        if callable(feature_cleanup):
            feature_cleanup()

        for child in feature_frame.winfo_children():
            child.destroy()

        create_window(parent_frame=feature_frame, filename=filename)
        feature_cleanup = getattr(feature_frame, "cleanup_emil", None)
        back_button = tk.Button(
            feature_frame,
            text="Retour au menu",
            command=show_menu,
            **secondary_button_style(),
        )
        back_button.pack(pady=10)
        feature_frame.tkraise()

    def open_simple_display():
        nonlocal feature_cleanup
        if callable(feature_cleanup):
            feature_cleanup()

        for child in feature_frame.winfo_children():
            child.destroy()

        create_window_simple_display(parent_frame=feature_frame)
        feature_cleanup = getattr(feature_frame, "cleanup_simple_display", None)
        back_button = tk.Button(
            feature_frame,
            text="Retour au menu",
            command=show_menu,
            **secondary_button_style(),
        )
        back_button.pack(pady=10)
        feature_frame.tkraise()

    def open_max():
        nonlocal feature_cleanup
        if callable(feature_cleanup):
            feature_cleanup()

        for child in feature_frame.winfo_children():
            child.destroy()

        create_window_max(parent_frame=feature_frame)
        feature_cleanup = getattr(feature_frame, "cleanup_max", None)
        back_button = tk.Button(
            feature_frame,
            text="Retour au menu",
            command=show_menu,
            **secondary_button_style(),
        )
        back_button.pack(pady=10)
        feature_frame.tkraise()

    def on_close_root():
        if callable(feature_cleanup):
            feature_cleanup()
        root.quit()
        root.destroy()
        os._exit(0)

    emil_button = tk.Button(
        menu_card,
        text="Emil",
        command=lambda: open_feature("utils/emil.sq"),
        **button_style(),
    )
    emil_button.pack(pady=10, padx=20, fill="x")

    seven_three_button = tk.Button(
        menu_card,
        text="7sec - 3sec",
        command=lambda: open_feature("utils/7_3.sq"),
        **button_style(),
    )
    seven_three_button.pack(pady=10, padx=20, fill="x")

    simple_display_button = tk.Button(
        menu_card,
        text="Simple Display",
        command=open_simple_display,
        **button_style(),
    )
    simple_display_button.pack(pady=10, padx=20, fill="x")

    max_button = tk.Button(
        menu_card,
        text="Max",
        command=open_max,
        **button_style(),
    )
    max_button.pack(pady=10, padx=20, fill="x")

    root.protocol("WM_DELETE_WINDOW", on_close_root)
    show_menu()
    root.mainloop()



if __name__ == "__main__":
    create_menu_window()
