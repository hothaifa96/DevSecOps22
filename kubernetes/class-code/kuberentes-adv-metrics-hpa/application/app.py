import os
import time
import math
import threading
from flask import Flask, jsonify

app = Flask(__name__)

load_level = 0
lock = threading.Lock()

BURN_MULTIPLIER = int(os.environ.get("BURN_MULTIPLIER", "1000"))
TICK = float(os.environ.get("BURN_TICK", "0.05"))
MAX_LEVEL = int(os.environ.get("BURN_MAX", "100"))


def cpu_burner():
    while True:
        with lock:
            level = load_level
        for _ in range(level * BURN_MULTIPLIER):
            math.sqrt(123456789.0)
        time.sleep(TICK)


@app.route("/")
def index():
    return "ok"


@app.route("/up/<int:n>")
def up(n):
    global load_level
    with lock:
        load_level = min(load_level + n, MAX_LEVEL)
    return jsonify({"level": load_level})


@app.route("/down/<int:n>")
def down(n):
    global load_level
    with lock:
        load_level = max(load_level - n, 0)
    return jsonify({"level": load_level})


@app.route("/status")
def status():
    return jsonify({"level": load_level})


burner = threading.Thread(target=cpu_burner, daemon=True)
burner.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)
