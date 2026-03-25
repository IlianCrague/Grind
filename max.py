import tkinter as tk
import asyncio
import threading
from datetime import datetime
from pathlib import Path
from bleak import BleakScanner
from ui_theme import (
    apply_window_theme,
    frame_style,
    label_style,
    button_style,
)


DEVICE_ADDRESS = "2A:C0:19:11:23:B7"
WEIGHT_OFFSET = 10
STABLE_OFFSET = 14

window_ref = None
weight_display = None
max_display = None
status_display = None
max_since_start = 0.0

BASE_DIR = Path(__file__).resolve().parent
MAX_DROITE_FILE = BASE_DIR / "utils" / "max_droite"
MAX_GAUCHE_FILE = BASE_DIR / "utils" / "max_gauche"


def advertisement_callback(device, advertisement_data):
    """Handle BLE advertisement data and update the current weight label."""
    global max_since_start

    if (
        device.address != DEVICE_ADDRESS
        or weight_display is None
        or max_display is None
        or window_ref is None
    ):
        return

    if not advertisement_data.manufacturer_data:
        return

    for _, data in advertisement_data.manufacturer_data.items():
        if len(data) > max(WEIGHT_OFFSET + 1, STABLE_OFFSET):
            weight = (data[WEIGHT_OFFSET] & 0xFF) << 8 | (data[WEIGHT_OFFSET + 1] & 0xFF)
            weight_kg = weight / 100
            max_since_start = max(max_since_start, weight_kg)

            # BLE callback runs outside Tk's main thread, so schedule UI update on Tk thread.
            window_ref.after(0, lambda w=weight_kg: weight_display.config(text=f"{w:.2f} kg"))
            window_ref.after(0, lambda m=max_since_start: max_display.config(text=f"Max : {m:.2f} kg"))
            break


def append_max_to_file(target_file):
    """Append a line with today's date and max since startup to a target file."""
    if status_display is None:
        return

    now = datetime.now().strftime("%Y-%m-%d")
    line = f"{now} {max_since_start:.2f}\n"

    try:
        target_file.parent.mkdir(parents=True, exist_ok=True)
        with target_file.open("a", encoding="utf-8") as file:
            file.write(line)
        status_display.config(text=f"Ajoute : {line.strip()}")
    except OSError as error:
        status_display.config(text=f"Erreur ecriture : {error}")

def get_max_from_file(target_file):
    """Read the last max value from a target file."""
    if not target_file.exists():
        return 0.0

    try:
        with target_file.open("r", encoding="utf-8") as file:
            lines = file.readlines()
            if not lines:
                return 0.0
            last_line = lines[-1].strip()
            parts = last_line.split()
            if len(parts) != 2:
                return 0.0
            return float(parts[1])
    except (OSError, ValueError):
        return 0.0


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


def create_window_max(parent_frame=None):
    global window_ref, weight_display, max_display, status_display

    if parent_frame is None:
        window = tk.Tk()
        window.title("Poids courant")
    else:
        window = parent_frame
    apply_window_theme(window)

    main_card = tk.Frame(window, **frame_style())
    main_card.pack(padx=24, pady=24, fill="both", expand=True)

    window_ref = window

    # Weight display
    weight_display = tk.Label(main_card, text="Deconnecte", **label_style("title"))
    weight_display.pack(pady=(24, 12))

    # Max display from file
    max_from_file_gauche = get_max_from_file(MAX_GAUCHE_FILE)
    max_from_file_droite = get_max_from_file(MAX_DROITE_FILE)
    max_from_file_display = tk.Label(main_card, text=f"Last MG : {max_from_file_gauche:.2f} kg   |   Last MD : {max_from_file_droite:.2f} kg", **label_style("muted"))
    max_from_file_display.pack(pady=6)



    # Max display from startup
    max_display = tk.Label(main_card, text="Max : 0.00 kg", **label_style("value"))
    max_display.pack(pady=6)

    # Save buttons
    buttons_frame = tk.Frame(main_card, bg="#252526")
    buttons_frame.pack(pady=10)

    add_left_button = tk.Button(
        buttons_frame,
        text="Ajouter max main gauche",
        command=lambda: append_max_to_file(MAX_GAUCHE_FILE),
        **button_style(),
    )
    add_left_button.pack(side=tk.LEFT, padx=6)

    add_right_button = tk.Button(
        buttons_frame,
        text="Ajouter max main droite",
        command=lambda: append_max_to_file(MAX_DROITE_FILE),
        **button_style(),
    )
    add_right_button.pack(side=tk.LEFT, padx=6)

    status_display = tk.Label(main_card, text="", **label_style("muted"))
    status_display.pack(pady=6)

    # Async event loop
    loop = asyncio.new_event_loop()
    stop_event = threading.Event()
    ble_thread = threading.Thread(target=run_asyncio, args=(loop, stop_event), daemon=True)
    ble_thread.start()

    def cleanup_max():
        stop_event.set()
        ble_thread.join(timeout=3)
        return not ble_thread.is_alive()

    # On close event (only for standalone windows)
    def on_close():
        cleanup_max()
        if isinstance(window, (tk.Tk, tk.Toplevel)):
            window.quit()

    if isinstance(window, (tk.Tk, tk.Toplevel)):
        window.protocol("WM_DELETE_WINDOW", on_close)
    else:
        window.cleanup_max = cleanup_max

    # If it's a standalone window, start the event loop
    if parent_frame is None:
        window.mainloop()


if __name__ == "__main__":
    create_window_max()
