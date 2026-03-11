from flask import Flask, Response, request
import threading
import time
import numpy as np
from PIL import ImageGrab
from lib.bmi.bmi.bmi import image_array_to_bmi_bytes

# ------------------
# config
# ------------------

PORT = 4335
FPS = 10

app = Flask(__name__)

last_frame = None
frame_lock = threading.Lock()
frame_event = threading.Event()  # pour notifier les nouvelles frames

# ------------------
# capture écran
# ------------------

def capture_loop():
    global last_frame

    delay = 1 / FPS

    while True:
        start = time.time()

        screenshot = ImageGrab.grab()
        frame = np.array(screenshot)

        with frame_lock:
            last_frame = frame
            frame_event.set()  # notifier qu'une nouvelle frame est disponible

        elapsed = time.time() - start
        time.sleep(max(0, delay - elapsed))


# ------------------
# API
# ------------------

@app.route("/get_frame")
def get_frame():

    width = request.args.get("width", type=int, default=200)
    height = request.args.get("height", type=int, default=111)

    # Attendre une nouvelle frame si aucune dispo
    frame_event.wait(timeout=1.0)  # max 1 sec d'attente
    frame_event.clear()

    with frame_lock:
        if last_frame is None:
            return Response(status=204)
        frame = last_frame.copy()

    try:
        bmi_bytes = image_array_to_bmi_bytes(frame, width, height)
    except Exception as e:
        return Response(str(e), status=500)

    return Response(bmi_bytes, mimetype="application/octet-stream")


# ------------------
# main
# ------------------

if __name__ == "__main__":

    threading.Thread(target=capture_loop, daemon=True).start()

    print("Screen stream server started")
    print(f"Port: {PORT}")

    app.run(host="0.0.0.0", port=PORT)