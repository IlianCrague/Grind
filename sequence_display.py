import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import asyncio
import threading
from bleak import BleakScanner


WEIGHT_OFFSET = 10
STABLE_OFFSET = 14
WEIGHT_MIN = 1
weights = []
max_weight = 0
timer_running = False
current_weight = 0

# Sequence : [(Active=True/False, Name, Duration in seconds, Weight Goal)]
SEQUENCE = [
    (True, "3 drag", 10, 23), (False, "Repos", 5), (True, "3 drag", 10, 23), (False, "Repos", 5), (True, "3 drag", 10, 23), (False, "Repos", 5),
    (True, "3 drag", 10, 23), (False, "Repos", 5), (True, "3 drag", 10, 23), (False, "Repos", 5), (True, "3 drag", 10, 23), (False, "Repos", 5),    
    (True, "2 drag", 10, 16), (False, "Repos", 5), (True, "2 drag", 10, 16), (False, "Repos", 5),
    (True, "2 drag", 10, 16), (False, "Repos", 5), (True, "2 drag", 10, 16), (False, "Repos", 5),
    (True, "4 crimp", 10, 27), (False, "Repos", 5), (True, "4 crimp", 10, 27), (False, "Repos", 5), (True, "4 crimp", 10, 27), (False, "Repos", 5), (True, "4 crimp", 10, 27), (False, "Repos", 5),
    (True, "4 crimp", 10, 27), (False, "Repos", 5), (True, "4 crimp", 10, 27), (False, "Repos", 5), (True, "4 crimp", 10, 27), (False, "Repos", 5), (True, "4 crimp", 10, 27), (False, "Repos", 5),
    (True, "back 3", 10, 21), (False, "Repos", 5), (True, "back 3", 10, 21), (False, "Repos", 5),
    (True, "back 3", 10, 21), (False, "Repos", 5), (True, "back 3", 10, 21), (False, "Repos", 5),
    (True, "middle 3", 10, 20), (False, "Repos", 5), (True, "middle 3", 10, 20), (False, "Repos", 5),
    (True, "middle 3", 10, 20), (False, "Repos", 5), (True, "middle 3", 10, 20), (False, "Repos", 5),
    (True, "mid 2", 10, 16), (False, "Repos", 5),
    (True, "mid 2", 10, 16), (False, "Repos", 5),
    (True, "front 2", 10, 21), (False, "Repos", 5),
    (True, "front 2", 10, 21), (False, "Repos", 5),
    ]
CURRENT_SEQUENCE = 0
STARTED = False
FINISHED = False
TIME_LEFT = SEQUENCE[CURRENT_SEQUENCE][2]  # Initial time for the current sequence


def update_graph(ax, canvas):
    """Updates the weight graph."""
    global CURRENT_SEQUENCE, SEQUENCE, max_weight
    ax.clear()
    if SEQUENCE[CURRENT_SEQUENCE][0]:
        ax.plot(range(len(weights)), [SEQUENCE[CURRENT_SEQUENCE][3] for _ in weights], color="red")
        ax.set_ylim(0, SEQUENCE[CURRENT_SEQUENCE][3] + 5)
    else :
        ax.set_ylim(0, max_weight // 100 + 10)
    ax.plot(range(len(weights)), weights, '-o', label="Poids (kg)", marker='', color="blue")
    ax.set_xlim(0, max(30, len(weights)))
    ax.set_ylabel("Poids (kg)")
    ax.legend()
    canvas.draw()


def start_timer():
    """Starts the timer for the current sequence step."""
    global timer_running, TIME_LEFT, CURRENT_SEQUENCE, STARTED

    if timer_running:  # Prevents multiple timers running in parallel
        return

    timer_running = True

    def next_sequence():
        """Switches to the next step in the sequence."""
        global CURRENT_SEQUENCE, TIME_LEFT, timer_running, STARTED, FINISHED
        if CURRENT_SEQUENCE < len(SEQUENCE) - 1:
            CURRENT_SEQUENCE += 1
            TIME_LEFT = SEQUENCE[CURRENT_SEQUENCE][2]
            timer_running = False  # Restart timer for the new step
            start_timer()
        else:
            timer_running = False  # Stops the timer when the sequence ends
            time_left.config(text="Séquence terminée")
            STARTED = True
            FINISHED = True

    def countdown():
        """Handles the countdown for the current step."""
        global TIME_LEFT, timer_running, current_weight

        # Check condition for the current mode
        if SEQUENCE[CURRENT_SEQUENCE][0]:  # Travail mode
            condition_met = current_weight > WEIGHT_MIN
        else:  # Repos mode
            condition_met = current_weight < WEIGHT_MIN

        if not condition_met:  # Pause the timer if the condition is not met
            timer_running = False
            return

        if TIME_LEFT > 0:
            time_left.config(text=f"{SEQUENCE[CURRENT_SEQUENCE][1]} : {TIME_LEFT:.1f} sec")
            TIME_LEFT -= 0.1
            time_left.after(100, countdown)  # Calls countdown after 0.1 second
        else:
            next_sequence()  # Moves to the next step

    countdown()


def advertisement_callback(device, advertisement_data):
    """Handles Bluetooth advertisement data."""
    global weights, max_weight, weight_display, timer_running, TIME_LEFT, STARTED, current_weight, FINISHED

    if device.address == "2A:C0:19:11:23:B7":
        if advertisement_data.manufacturer_data:
            for manufacturer_id, data in advertisement_data.manufacturer_data.items():
                if len(data) > max(WEIGHT_OFFSET + 1, STABLE_OFFSET):
                    weight = (data[WEIGHT_OFFSET] & 0xff) << 8 | (data[WEIGHT_OFFSET + 1] & 0xff)
                    weight_kg = weight / 100
                    current_weight = weight_kg  # Update current weight

                    # Update max weight
                    if weight > max_weight:
                        max_weight = weight

                    # Update weight display
                    weight_display.config(text=f"{weight_kg:.2f} kg     Max : {max_weight / 100:.2f} kg")

                    # Logic for starting/stopping timer based on weight and SEQUENCE
                    if SEQUENCE[CURRENT_SEQUENCE][0]:  # Travail mode
                        if weight_kg > WEIGHT_MIN:  # Condition met
                            if not timer_running:  # Restart timer if paused
                                if not STARTED:
                                    TIME_LEFT = SEQUENCE[CURRENT_SEQUENCE][2]
                                    STARTED = True
                                start_timer()

                    else:  # Repos mode
                        if weight_kg < WEIGHT_MIN:  # Condition met
                            if not timer_running:  # Restart timer if paused
                                if not STARTED:
                                    TIME_LEFT = SEQUENCE[CURRENT_SEQUENCE][2]
                                    STARTED = True
                                start_timer()
                    if timer_running or not STARTED or FINISHED :
                        weights.append(weight_kg)
                        update_graph(ax, canvas)


async def scan_for_advertisements():
    """Scans for BLE advertisements."""
    scanner = BleakScanner()
    scanner.register_detection_callback(advertisement_callback)

    await scanner.start()
    await asyncio.sleep(30)  # Scan for 30 seconds
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
