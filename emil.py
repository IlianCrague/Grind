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
timer_running = False
LENGTH_TAB = 20

# Sequence : [(Active=True/False, Name, Duration in seconds, Weight Goal)]
SEQUENCE = Sequence.from_file("utils/emil.sq")
CURRENT_SEQUENCE = 0
STARTED = False
FINISHED = False
TIME_LEFT = SEQUENCE.time  # Initial time for the current sequence

def update_graph(ax, canvas):
    """Updates the weight graph."""
    global CURRENT_SEQUENCE, SEQUENCE, max_weight, LENGTH_TAB
    ax.clear()
    if STARTED and not FINISHED and SEQUENCE.actif:
        ax.plot(range(LENGTH_TAB), [SEQUENCE.weight_goal] * LENGTH_TAB, color="red", label="Objectif (kg)")
        ax.set_ylim(0, SEQUENCE.weight_goal + 5)
    else:
        ax.set_ylim(0, max(max_weight / 100 + 10, 10))

    ax.plot(range(len(weights)), weights, '-o', label="Poids (kg)", color="blue", marker='')

    # Adjust x-axis dynamically
    ax.set_xlim(0, LENGTH_TAB)
    ax.set_ylabel("Poids (kg)")
    ax.legend()
    canvas.draw()



def start_timer():
    global timer_running, TIME_LEFT, CURRENT_SEQUENCE, STARTED

    if timer_running or FINISHED:  # Prevent multiple timers
        return

    timer_running = True

    def next_sequence():
        """Move to the next sequence step or finish."""
        global CURRENT_SEQUENCE, TIME_LEFT, timer_running, STARTED, FINISHED
        if not Sequence.next == None:
            CURRENT_SEQUENCE += 1
            TIME_LEFT = SEQUENCE.time
        else:
            timer_running = False
            time_left.config(text="Séquence terminée")
            STARTED = True
            FINISHED = True

    def countdown():
        """Countdown logic for the timer."""
        global TIME_LEFT, timer_running

        if FINISHED:  # Stop if finished
            return

        if timer_running and TIME_LEFT > 0:
            next = SEQUENCE.next.name if SEQUENCE.next is not None else "Finished"
            time_left.config(text=f"{SEQUENCE.name} : {TIME_LEFT:.1f} sec \n\n  next : {next}")
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
                    if not FINISHED and (SEQUENCE.actif and weight_kg > WEIGHT_MIN or not SEQUENCE.actif and weight_kg <= WEIGHT_MIN) :
                            if not timer_running:  # Restart timer if paused
                                if not STARTED:
                                    TIME_LEFT = SEQUENCE.time
                                    STARTED = True
                                start_timer()
                    else :
                        timer_running = False
                    if timer_running or not STARTED or FINISHED :
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


def create_window():
    """Creates the main application window."""
    global ax, canvas, weight_display, time_left
    window = tk.Tk()
    window.title("Poids Mesuré")

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

    # On close event
    def on_close():
        stop_event.set()
        window.quit()

    window.protocol("WM_DELETE_WINDOW", on_close)
    window.mainloop()


if __name__ == "__main__":
    create_window()
