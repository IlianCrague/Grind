import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import asyncio
import threading
import os
from bleak import BleakScanner
from sequence import Sequence
from ui_theme import (
    apply_window_theme,
    frame_style,
    label_style,
    apply_matplotlib_dark,
)


WEIGHT_OFFSET = 10
STABLE_OFFSET = 14
WEIGHT_MIN = 1
weights = []
max_weight = 0
timer_running = False
LENGTH_TAB = 20
SEQUENCE = None
TIME_LEFT = 0

# Sequence : [(Active=True/False, Name, Duration in seconds, Weight Goal)]
# SEQUENCE = Sequence.from_file("utils/emil.sq")
# SEQUENCE = Sequence.from_file("utils/7_3.sq")
# SEQUENCE = Sequence.from_file("utils/pinch_lift.sq")

STARTED = False
FINISHED = False


def update_graph(ax, canvas):
    """Updates the weight graph."""
    global SEQUENCE, max_weight, LENGTH_TAB
    ax.clear()
    apply_matplotlib_dark(ax.figure, ax)
    if STARTED and not FINISHED and SEQUENCE.actif:
        ax.plot(range(LENGTH_TAB), [SEQUENCE.weight_goal] * LENGTH_TAB, color="#f14c4c", label="Objectif (kg)")
        ax.set_ylim(0, SEQUENCE.weight_goal + 5)
    else:
        ax.set_ylim(0, max(max_weight / 100 + 10, 10))

    ax.plot(range(len(weights)), weights, label="Poids (kg)", color="#4fc1ff", marker='')

    # Adjust x-axis dynamically
    ax.set_xlim(0, LENGTH_TAB)
    ax.set_ylabel("Poids (kg)")
    ax.legend()
    canvas.draw()



def start_timer():
    global timer_running, TIME_LEFT, SEQUENCE, STARTED

    if timer_running or FINISHED:  # Prevent multiple timers
        return

    timer_running = True

    def next_sequence():
        """Move to the next sequence step or finish."""
        global SEQUENCE, TIME_LEFT, timer_running, STARTED, FINISHED
        if SEQUENCE.next is not None:
            SEQUENCE = SEQUENCE.next
            TIME_LEFT = SEQUENCE.time
        else:
            timer_running = False
            time_left.config(text="Séquence terminée")
            STARTED = True
            FINISHED = True

    def countdown():
        """Countdown logic for the timer."""
        global TIME_LEFT, timer_running, SEQUENCE

        if FINISHED:  # Stop if finished
            return

        if timer_running and TIME_LEFT > 0:
            next_name = SEQUENCE.next.name if SEQUENCE.next is not None else "Finished"
            time_left.config(text=f"{SEQUENCE.name} : {TIME_LEFT:.1f} sec \n\n  next : {next_name}")
            TIME_LEFT -= .1
            time_left.after(100, countdown)
        if TIME_LEFT < 0.1:
            next_sequence()

    countdown()



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

                    # Logic for starting/stopping timer based on weight and SEQUENCE
                    if not FINISHED and (SEQUENCE.actif and weight_kg > WEIGHT_MIN or not SEQUENCE.actif and weight_kg <= WEIGHT_MIN):
                        if not timer_running:  # Restart timer if paused
                            if not STARTED:
                                TIME_LEFT = SEQUENCE.time
                                STARTED = True
                            start_timer()
                    else:
                        timer_running = False
                    if timer_running or not STARTED or FINISHED:
                        weights.append(weight_kg)
                        if len(weights) > LENGTH_TAB:
                            weights.pop(0)
                        update_graph(ax, canvas)


async def scan_for_advertisements(stop_event):
    """Scans for BLE advertisements."""
    scanner = BleakScanner(detection_callback=advertisement_callback)

    await scanner.start()
    try:
        while not stop_event.is_set():
            await asyncio.sleep(0.2)
    finally:
        await scanner.stop()



def run_asyncio(loop, stop_event):
    """Runs the asyncio event loop."""
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(scan_for_advertisements(stop_event))
    finally:
        loop.close()



def create_window(parent_frame=None, filename=None):
    global ax, canvas, weight_display, time_left, SEQUENCE, TIME_LEFT

    if parent_frame is None:
        window = tk.Tk()
    else:
        window = parent_frame
    apply_window_theme(window)

    SEQUENCE = Sequence.from_file(filename)
    TIME_LEFT = SEQUENCE.time  # Initial time for the current sequence

    # Weight display
    main_card = tk.Frame(window, **frame_style())
    main_card.pack(padx=24, pady=24, fill="both", expand=True)

    weight_display = tk.Label(main_card, text="Deconnecte", **label_style("value"))
    weight_display.pack(pady=(20, 12))

    # Time left display
    time_left = tk.Label(main_card, text="- sec", **label_style("value"))
    time_left.pack(pady=(0, 20))

    # Graph frame
    canvas_frame = tk.Frame(main_card, bg="#252526")
    canvas_frame.pack(padx=20, pady=(0, 20), fill="both", expand=True)

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

    def cleanup_ble():
        stop_event.set()
        ble_thread.join(timeout=3)
        return not ble_thread.is_alive()

    # On close event (only for standalone windows)
    def on_close():
        cleanup_ble()
        if isinstance(window, (tk.Tk, tk.Toplevel)):
            window.quit()
            window.destroy()
            os._exit(0)

    if isinstance(window, (tk.Tk, tk.Toplevel)):
        window.protocol("WM_DELETE_WINDOW", on_close)
    else:
        window.cleanup_emil = cleanup_ble

    # If it's a standalone window, start the event loop
    if parent_frame is None:
        window.mainloop()


if __name__ == "__main__":
    create_window(filename="utils/emil.sq")
