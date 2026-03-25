import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import asyncio
import threading
from bleak import BleakScanner
from sequence import Sequence
from ui_theme import (
    apply_window_theme,
    frame_style,
    label_style,
    button_style,
    entry_style,
    apply_matplotlib_dark,
)


WEIGHT_OFFSET = 10
STABLE_OFFSET = 14
WEIGHT_MIN = 1
weights = []
max_weight = 0

LENGTH_TAB = 20

WEIGHT_GOAL = 40

def update_graph(ax, canvas):
    global WEIGHT_GOAL, max_weight, LENGTH_TAB
    ax.clear()
    apply_matplotlib_dark(ax.figure, ax)

    ax.set_ylim(0, WEIGHT_GOAL + 10, 10)
    if WEIGHT_GOAL > 0:
        ax.plot(range(LENGTH_TAB), [WEIGHT_GOAL] * LENGTH_TAB, color="#f14c4c", label="Objectif (kg)")

    ax.plot(range(len(weights)), weights, color="#4fc1ff", marker='')

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
                    weight_display.config(text=f"{weight_kg:.2f} kg     Max : {max_weight / 100:.2f} kg\n\n Max local : {max(weights) if len(weights) > 0 else 0} kg")

                    weights.append(weight_kg)
                    if len(weights) > LENGTH_TAB:
                        weights.pop(0)
                    update_graph(ax, canvas)


async def scan_for_advertisements():
    """Scans for BLE advertisements."""
    scanner = BleakScanner(detection_callback=advertisement_callback)

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
    apply_window_theme(window)

    main_card = tk.Frame(window, **frame_style())
    main_card.pack(padx=24, pady=24, fill="both", expand=True)

    # Weight display
    weight_display = tk.Label(main_card, text="Deconnecte", **label_style("value"))
    weight_display.pack(pady=(20, 12))

    # Time left display
    time_left = tk.Label(main_card, text="Suivi en direct", **label_style("muted"))
    time_left.pack(pady=(0, 16))

    # Weight goal controls
    goal_frame = tk.Frame(main_card, bg="#252526")
    goal_frame.pack(pady=10)

    goal_label = tk.Label(goal_frame, text="Weight goal (kg):", **label_style("body"))
    goal_label.pack(side=tk.LEFT, padx=(0, 8))

    goal_value = tk.StringVar(value=str(WEIGHT_GOAL))
    goal_entry = tk.Entry(goal_frame, textvariable=goal_value, width=10, **entry_style())
    goal_entry.pack(side=tk.LEFT)

    def apply_weight_goal(event=None):
        global WEIGHT_GOAL
        try:
            new_goal = float(goal_value.get().strip())
            if new_goal < 0:
                raise ValueError
            WEIGHT_GOAL = new_goal
            update_graph(ax, canvas)
        except ValueError:
            goal_value.set(str(WEIGHT_GOAL))

    apply_goal_button = tk.Button(goal_frame, text="Appliquer", command=apply_weight_goal, **button_style())
    apply_goal_button.pack(side=tk.LEFT, padx=(8, 0))
    goal_entry.bind("<Return>", apply_weight_goal)

    # Graph frame
    canvas_frame = tk.Frame(main_card, bg="#252526")
    canvas_frame.pack(padx=20, pady=20, fill="both", expand=True)

    # Plot setup
    fig, ax_ = plt.subplots(figsize=(5, 4))
    ax = ax_
    apply_matplotlib_dark(fig, ax)
    canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
    canvas.get_tk_widget().configure(bg="#252526", highlightthickness=0, bd=0)
    canvas.get_tk_widget().pack()

    # Async event loop
    loop = asyncio.new_event_loop()
    stop_event = threading.Event()
    ble_thread = threading.Thread(target=run_asyncio, args=(loop, stop_event), daemon=True)
    ble_thread.start()

    def cleanup_simple_display():
        stop_event.set()
        ble_thread.join(timeout=3)
        return not ble_thread.is_alive()

    # On close event (only for standalone windows)
    def on_close():
        cleanup_simple_display()
        if isinstance(window, (tk.Tk, tk.Toplevel)):
            window.quit()

    if isinstance(window, (tk.Tk, tk.Toplevel)):
        window.protocol("WM_DELETE_WINDOW", on_close)
    else:
        window.cleanup_simple_display = cleanup_simple_display

    # If it's a standalone window, start the event loop
    if parent_frame is None:
        window.mainloop()


if __name__ == "__main__":
    create_window_simple_display()
