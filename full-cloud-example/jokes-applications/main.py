from flask import Flask, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)


@app.route("/joke")
def get_joke():
    res = requests.get("https://api.chucknorris.io/jokes/random")

    if res.status_code != 200:
        return jsonify({"error": "Failed to get joke"}), 500

    data = res.json()

    return jsonify({
        "joke": data["value"]
    })


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)