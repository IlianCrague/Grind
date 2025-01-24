import tkinter as tk
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import asyncio
import threading
from bleak import BleakScanner
import random

# Paramètres
WEIGHT_OFFSET = 10
STABLE_OFFSET = 14
WEIGHT_MIN = 1
MAX_WEIGHT = 0
LENGTH = 15
POS_BIRD = 5
MIN_Y = 0
MAX_Y = 25
WIDTH_PIPE = 2
X_PIPE = LENGTH
Y_PIPE = 15
SCORE = 0
FINISHED = False
N = 0
weights = []
LENGTH_TAB = 2

# Variables globales
STARTED = False
pipes = []  # Liste des tuyaux visibles
current_weight = 0  # Initialisation de current_weight

# Fonction de mise à jour du graphique
def update_graph(ax, canvas):
    """Mise à jour du graphique."""
    global current_weight, POS_BIRD

    ax.clear()

    # Affiche le poids mesuré
    h = MAX_WEIGHT if current_weight > MAX_WEIGHT else current_weight
    
    ax.plot([POS_BIRD - i for i in range(LENGTH_TAB)], weights, color="red", marker='')

    # Ajuste l'échelle des axes
    ax.set_xlim(0, LENGTH)
    ax.set_ylim(MIN_Y, MAX_Y)

    # Dessine les tuyaux
    for pipe in pipes:
        if pipe[2]:
            rect = patches.Rectangle((pipe[0], pipe[1]), WIDTH_PIPE, MAX_Y - pipe[1], linewidth=1, edgecolor='green', facecolor='none')
        else:
            rect = patches.Rectangle((pipe[0], 0), WIDTH_PIPE, pipe[1], linewidth=1, edgecolor='green', facecolor='none')
        ax.add_patch(rect)

    canvas.draw()

def check_dead():
    global current_weight, X_PIPE, Y_PIPE, pipes
    for pipe in pipes:
        if POS_BIRD >= pipe[0] and POS_BIRD <= pipe[0] + WIDTH_PIPE: #same x
            if pipe[2]:
                if current_weight >= pipe[1]:
                    return True
            else :
                if current_weight <= pipe[1]:
                    return True
    return False

# Callback Bluetooth pour récupérer le poids
def advertisement_callback(device, advertisement_data):
    """Gère les données de publicité Bluetooth."""
    global current_weight, STARTED, Y_PIPE, X_PIPE, pipes, SCORE, FINISHED, N
    
    if device.address == "2A:C0:19:11:23:B7":
        if advertisement_data.manufacturer_data:
            for manufacturer_id, data in advertisement_data.manufacturer_data.items():
                if len(data) > max(WEIGHT_OFFSET + 1, STABLE_OFFSET):
                    if N < 25:
                        N+=1
                
                    weight = (data[WEIGHT_OFFSET] & 0xff) << 8 | (data[WEIGHT_OFFSET + 1] & 0xff)
                    current_weight = weight / 100
                    weights.append(current_weight)
                    if len(weights) > LENGTH_TAB:
                        weights.pop(0)


                    weight_display.config(text=f"{current_weight:.2f} kg \n\n Score : {SCORE} pts")


                    if not FINISHED and (len(pipes) == 0 or pipes[-1][0] < LENGTH - 7):  # Ajoute un tuyau si l'écran a de la place
                        Y_PIPE = random.randint(MIN_Y + (MAX_Y - MIN_Y) // 4, MAX_Y - (MAX_Y - MIN_Y) // 4)
                        X_PIPE = LENGTH
                        if N > 20:
                            pipes.append([X_PIPE, Y_PIPE, random.choice([1, 0])])


                    for pipe in pipes:
                        pipe[0] -= 1


                    if len(pipes) > 0 and pipes[0][0] < 0:
                        SCORE += 1
                        pipes = pipes[1:]

                    if check_dead():
                        FINISHED = True
                        pipes = []

                    update_graph(ax, canvas)



async def scan_for_advertisements():
    """Recherche les publicités Bluetooth."""
    scanner = BleakScanner()
    scanner.register_detection_callback(advertisement_callback)

    await scanner.start()
    await asyncio.sleep(600)
    await scanner.stop()

# Fonction pour exécuter l'événement asynchrone dans un thread
def run_asyncio(loop, stop_event):
    """Exécute la boucle d'événements asyncio."""
    asyncio.set_event_loop(loop)
    loop.create_task(scan_for_advertisements())

    while not stop_event.is_set():
        loop.call_soon(loop.stop)
        loop.run_forever()

# Fonction pour créer la fenêtre de l'application
def create_window_flappy_bird(parent_frame=None):
    global ax, canvas, weight_display, time_left

    if parent_frame is None:
        window = tk.Tk()
    else:
        window = parent_frame

    # Weight display
    weight_display = tk.Label(window, text="Déconnecté", font=("Helvetica", 16))
    weight_display.pack(pady=20)

    # Time left display
    time_left = tk.Label(window, text="- sec", font=("Helvetica", 16))
    time_left.pack(pady=20)

    # Graph frame
    canvas_frame = tk.Frame(window)
    canvas_frame.pack(padx=20, pady=20)

    # Plot setup
    fig, ax_ = plt.subplots(figsize=(5, 4))
    ax = ax_
    canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
    canvas.get_tk_widget().pack()

    # Async event loop
    loop = asyncio.new_event_loop()
    stop_event = threading.Event()
    threading.Thread(target=run_asyncio, args=(loop, stop_event), daemon=True).start()

    # On close event (only for standalone windows)
    def on_close():
        stop_event.set()
        if isinstance(window, (tk.Tk, tk.Toplevel)):
            window.quit()

    if isinstance(window, (tk.Tk, tk.Toplevel)):
        window.protocol("WM_DELETE_WINDOW", on_close)

    # If it's a standalone window, start the event loop
    if parent_frame is None:
        window.mainloop()

# Exécution de l'application
if __name__ == "__main__":
    create_window_flappy_bird()
