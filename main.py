"""
main.py  –  Flask API server
=============================
Contains:
  - Flask app & CORS setup
  - All REST endpoints (/api/upload, /api/chat, /api/status, /api/history, /api/reset)
  - Server startup with default CSV auto-load

All AI / agent logic lives in app.py.
"""

import os
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS

# Import everything from the agent module
import app as agent

flask_app = Flask(__name__)
CORS(flask_app)

UPLOAD_FOLDER = "./uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ── Routes ────────────────────────────────────────────────────────────────────

@flask_app.route("/", methods=["GET"])
def home():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        return f"Error loading index.html: {str(e)}", 500


@flask_app.route("/api/upload", methods=["POST"])
def upload_csv():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    if not file.filename.lower().endswith(".csv"):
        return jsonify({"error": "Only CSV files are supported"}), 400

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    try:
        df = pd.read_csv(filepath)
        # Reset previous session, then build fresh agent for new file
        agent.reset_session()
        agent.build_agent(df)
        agent.set_filename(file.filename)

        return jsonify({
            "message":  "CSV uploaded and agent ready!",
            "filename": file.filename,
            "shape":    list(df.shape),
            "columns":  list(df.columns),
            "preview":  df.head(5).to_dict(orient="records"),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@flask_app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "No message provided"}), 400

    user_message = data["message"].strip()
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    try:
        answer = agent.run_query(user_message)
        agent.append_history("user",      user_message)
        agent.append_history("assistant", answer)
        return jsonify({"answer": answer})
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@flask_app.route("/api/status", methods=["GET"])
def status():
    return jsonify(agent.get_session_state())


@flask_app.route("/api/history", methods=["GET"])
def history():
    return jsonify({"history": agent.get_history()})


@flask_app.route("/api/reset", methods=["POST"])
def reset():
    agent.reset_session()
    return jsonify({"message": "Session reset successfully."})


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Auto-load the default CSV if present
    default_csv = "./credit_risk_dataset.csv"
    if os.path.exists(default_csv):
        df = pd.read_csv(default_csv)
        agent.build_agent(df)
        agent.set_filename("credit_risk_dataset.csv")
        print(f"[OK] Loaded default CSV: {default_csv} | Shape: {df.shape}")

    print("[*] Starting CSV AI Agent API on http://localhost:8000")
    flask_app.run(debug=True, port=8000)
