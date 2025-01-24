import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import asyncio
import threading
from bleak import BleakScanner
from sequence import Sequence


WEIGHT_OFFSET = 10
STABLE_OFFSET = 14
WEIGHT_MIN = 1
weights = []
max_weight = 0

LENGTH_TAB = 20

def update_graph(ax, canvas):
    global SEQUENCE, max_weight, LENGTH_TAB
    ax.clear()

    ax.set_ylim(0, max(max_weight / 100 + 10, 10))

    ax.plot(range(len(weights)), weights, color="blue", marker='')

    # Adjust x-axis dynamically
    ax.set_xlim(0, LENGTH_TAB)
    ax.set_ylabel("Poids (kg)")
    canvas.draw()

def advertisement_callback(device, advertisement_data):
    """Handles Bluetooth advertisement data."""
    global weights, max_weight, weight_display, timer_running, TIME_LEFT, STARTED, FINISHED

    if device.address == "2A:C0:19:11:23:B7":
        if advertisement_data.manufacturer_data:
            for manufacturer_id, data in advertisement_data.manufacturer_data.items():
                if len(data) > max(WEIGHT_OFFSET + 1, STABLE_OFFSET):
                    weight = (data[WEIGHT_OFFSET] & 0xff) << 8 | (data[WEIGHT_OFFSET + 1] & 0xff)
                    weight_kg = weight / 100


                    # Update max weight
                    if weight > max_weight:
                        max_weight = weight

                    # Update weight display
                    weight_display.config(text=f"{weight_kg:.2f} kg     Max : {max_weight / 100:.2f} kg")

                    weights.append(weight_kg)
                    if len(weights) > LENGTH_TAB:
                        weights.pop(0)
                    update_graph(ax, canvas)


async def scan_for_advertisements():
    """Scans for BLE advertisements."""
    scanner = BleakScanner()
    scanner.register_detection_callback(advertisement_callback)

    await scanner.start()
    await asyncio.sleep(600)
    await scanner.stop()


def run_asyncio(loop, stop_event):
    """Runs the asyncio event loop."""
    asyncio.set_event_loop(loop)
    loop.create_task(scan_for_advertisements())

    while not stop_event.is_set():
        loop.call_soon(loop.stop)
        loop.run_forever()


def create_window_simple_display(parent_frame=None):
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


if __name__ == "__main__":
    create_window_simple_display()
