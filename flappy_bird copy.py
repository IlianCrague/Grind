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
LENGTH = 30
POS_LEFT_PLAYER = 3
POS_RIGHT_PLAYER = LENGTH - POS_LEFT_PLAYER
MIN_Y = 0
MAX_Y = 10
SCORE = 0
FINISHED = False
WEIGHT_LEFT_PLAYER = 0
WEIGHT_RIGHT_PLAYER = 0
#ball = (x, y, x_speed, y_speed)
BALL = [LENGTH // 2, (MAX_Y + MIN_Y) / 2, 0, 0]
taille_raquette = 2

# Fonction de mise à jour du graphique
def update_graph(ax, canvas):
    """Mise à jour du graphique."""
    global current_weight, WEIGHT_LEFT_PLAYER, WEIGHT_RIGHT_PLAYER, taille_raquette

    ax.clear()

    if not FINISHED:
        ax.plot(BALL[0], BALL[1], 'ro')

    ax.plot([POS_LEFT_PLAYER, POS_LEFT_PLAYER], [WEIGHT_LEFT_PLAYER - taille_raquette, WEIGHT_LEFT_PLAYER + taille_raquette], color="red", marker='')

    ax.plot([POS_RIGHT_PLAYER, POS_RIGHT_PLAYER], [WEIGHT_RIGHT_PLAYER - taille_raquette, WEIGHT_RIGHT_PLAYER + taille_raquette], color="blue", marker='')

    # Ajuste l'échelle des axes
    ax.set_xlim(0, LENGTH)
    ax.set_ylim(MIN_Y, MAX_Y)

    canvas.draw()

def move_ball():
    global BALL, taille_raquette, SCORE
    if BALL[0] + BALL[2] <= POS_LEFT_PLAYER :#post left player
        if BALL[1] > WEIGHT_LEFT_PLAYER + taille_raquette or BALL[1] < WEIGHT_LEFT_PLAYER - taille_raquette :#dead
            return False
        else:
            BALL[2] = BALL[2] * -1
            SCORE += 1
    if BALL[0] + BALL[2] >= POS_RIGHT_PLAYER : #post right player
        if BALL[1] > WEIGHT_RIGHT_PLAYER + taille_raquette or BALL[1] < WEIGHT_RIGHT_PLAYER - taille_raquette :#dead
            return False
        else:
            BALL[2] = BALL[2] * -1
            SCORE += 1
    if  BALL[1] + BALL[3] >= MAX_Y or BALL[1] + BALL[3] <= MIN_Y: #hit ceiling or ground
        BALL[3] = BALL[3] * -1
    BALL[0] += BALL[2]
    BALL[1] += BALL[3]
    return True


# Callback Bluetooth pour récupérer le poids
def advertisement_callback(device, advertisement_data):
    """Gère les données de publicité Bluetooth."""
    global WEIGHT_LEFT_PLAYER, WEIGHT_RIGHT_PLAYER, pipes, SCORE, FINISHED, BALL

    if device.address == "2A:C0:19:11:23:A7" :
        if advertisement_data.manufacturer_data:
            for manufacturer_id, data in advertisement_data.manufacturer_data.items():
                if len(data) > max(WEIGHT_OFFSET + 1, STABLE_OFFSET):
                
                    WEIGHT_RIGHT_PLAYER = ((data[WEIGHT_OFFSET] & 0xff) << 8 | (data[WEIGHT_OFFSET + 1] & 0xff)) / 100
                    update_graph(ax, canvas)

    if device.address == "2A:C0:19:11:23:B7" :
        if advertisement_data.manufacturer_data:
            for manufacturer_id, data in advertisement_data.manufacturer_data.items():
                if len(data) > max(WEIGHT_OFFSET + 1, STABLE_OFFSET):
                
                    WEIGHT_LEFT_PLAYER = ((data[WEIGHT_OFFSET] & 0xff) << 8 | (data[WEIGHT_OFFSET + 1] & 0xff)) / 100

                    if BALL[2] == 0:
                        BALL[2] = random.choice([-1, 1])
                        BALL[3] = random.choice([-2, -1, 1, 2])

                    if not FINISHED :
                        if not move_ball():
                            FINISHED = True

                    weight_display.config(text=f"Left Player :{WEIGHT_LEFT_PLAYER:.2f} kg \n\n Right Player :{WEIGHT_RIGHT_PLAYER:.2f} kg \n\n Score : {SCORE} pts")


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
    time_left = tk.Label(window, text="", font=("Helvetica", 16))
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
