import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import asyncio
import threading
from bleak import BleakScanner

WEIGHT_OFFSET = 10
STABLE_OFFSET = 14
weights = []
max_weight = 0

def update_graph(ax, canvas):
    ax.clear()  # Effacer l'ancien graphique
    ax.plot(range(len(weights)), weights, '-o', label="Poids (kg)", marker='')
    ax.set_xlim(0, max(30, len(weights)))  # Limite de 30 points visibles
    ax.set_ylim(0, max(weights) + 10)  # Ajuste automatiquement l'échelle si nécessaire
    ax.set_ylabel("Poids (kg)")
    ax.legend()
    canvas.draw()

def advertisement_callback(device, advertisement_data):
    global weights, max_weight, label
    if device.address == "2A:C0:19:11:23:B7":
        if advertisement_data.manufacturer_data:
            for manufacturer_id, data in advertisement_data.manufacturer_data.items():
                if len(data) > max(WEIGHT_OFFSET + 1, STABLE_OFFSET):
                    weight = (data[WEIGHT_OFFSET] & 0xff) << 8 | (data[WEIGHT_OFFSET + 1] & 0xff)

                    if weight > max_weight:
                        max_weight = weight

                    label.config(text=f"{weight/100:.2f} kg     Max : {max_weight/100:.2f} kg")
                    
                    if weight != 0 or weight == 0 and len(weights) > 0 and weights[-1] != 0:
                        weights.append(weight / 100)
                        update_graph(ax, canvas)



async def scan_for_advertisements():
    scanner = BleakScanner()
    scanner.register_detection_callback(advertisement_callback)

    await scanner.start()
    await asyncio.sleep(30)  # Scanner pendant 30 secondes
    await scanner.stop()

def run_asyncio(loop, stop_event):
    asyncio.set_event_loop(loop)

    loop.create_task(scan_for_advertisements())

    while not stop_event.is_set():
        loop.call_soon(loop.stop)
        loop.run_forever()

def create_window():
    global ax, canvas, label
    window = tk.Tk()
    window.title("Poids Mesuré")

    label = tk.Label(window, text="0.00 kg", font=("Helvetica", 16))
    label.pack(pady=20)

    canvas_frame = tk.Frame(window)
    canvas_frame.pack(padx=20, pady=20)

    fig, ax_ = plt.subplots(figsize=(5, 4))
    ax = ax_
    canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
    canvas.get_tk_widget().pack()

    loop = asyncio.new_event_loop()

    stop_event = threading.Event()

    threading.Thread(target=run_asyncio, args=(loop, stop_event), daemon=True).start()

    def on_close():
        stop_event.set()
        window.quit()
    window.protocol("WM_DELETE_WINDOW", on_close)

    window.mainloop()

if __name__ == "__main__":
    create_window()

