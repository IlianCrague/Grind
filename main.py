import tkinter as tk
import asyncio
import sys

# Exemple de création de fenêtres d'Emil et d'affichage simple, ces fonctions doivent être implémentées
from emil import create_window_emil
from simple_display import create_window_simple_display

def show_frame(frame):
    """Affiche un cadre spécifique."""
    frame.tkraise()

def create_window():
    # Création de la fenêtre principale
    root = tk.Tk()
    root.title("Grind")
    root.geometry("800x600")

    # Configuration des cadres
    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)

    # Création des cadres
    home_frame = tk.Frame(root)
    emil_frame = tk.Frame(root)
    simple_display_frame = tk.Frame(root)

    for frame in (home_frame, emil_frame, simple_display_frame):
        frame.grid(row=0, column=0, sticky="nsew")

    # Contenu de la page d'accueil
    emil_button = tk.Button(
        home_frame, text="Emil", font=("Helvetica", 12),
        command=lambda: show_frame(emil_frame)  # Affiche le cadre Emil
    )
    emil_button.pack(pady=10)

    simple_display_button = tk.Button(
        home_frame, text="Simple Display", font=("Helvetica", 12),
        command=lambda: show_frame(simple_display_frame)  # Affiche le cadre Simple Display
    )
    simple_display_button.pack(pady=10)

    # Bouton pour revenir à la page d'accueil depuis Emil
    emil_back_button = tk.Button(
        emil_frame, text="Retour", font=("Helvetica", 12),
        command=lambda: show_frame(home_frame)  # Retourne au cadre d'accueil
    )
    emil_back_button.pack(pady=10)

    simple_display_back_button = tk.Button(
        simple_display_frame, text="Retour", font=("Helvetica", 12),
        command=lambda: show_frame(home_frame)  # Retourne au cadre d'accueil
    )
    simple_display_back_button.pack(pady=10)

    # Ajoutez des fenêtres de contenu dans les cadres
    create_window_emil(emil_frame)
    create_window_simple_display(simple_display_frame)

    # Assurez-vous que la fenêtre "home_frame" est affichée par défaut
    show_frame(home_frame)

    # Gérer la fermeture de la fenêtre
    def on_close():
        root.quit()
        sys.exit(0)

    root.protocol("WM_DELETE_WINDOW", on_close)

    root.mainloop()

if __name__ == "__main__":
    create_window()
