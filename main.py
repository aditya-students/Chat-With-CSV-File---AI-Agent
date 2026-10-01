"""
main.py  –  Flask API server (Production Ready for Render)
=========================================================
Contains:
  - Flask app & CORS setup
  - REST endpoints (/health, /, /api/upload, /api/chat, /api/status, /api/history, /api/reset)
  - Module-level default CSV auto-load
"""

import os
import logging
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Import everything from the agent module
import app as agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

flask_app = Flask(__name__)
CORS(flask_app)
flask_app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20 MB limit


# ── Default CSV Auto-load ─────────────────────────────────────────────────────

def load_default_csv():
    default_csv = os.path.join(BASE_DIR, "credit_risk_dataset.csv")
    if os.path.exists(default_csv):
        try:
            df = pd.read_csv(default_csv)
            agent.build_agent(df)
            agent.set_filename("credit_risk_dataset.csv")
            logger.info(f"[OK] Loaded default CSV: {default_csv} | Shape: {df.shape}")
        except Exception as e:
            logger.error(f"Failed to auto-load default CSV: {e}")

# Module-level auto-load for Gunicorn / WSGI
load_default_csv()


# ── Routes ────────────────────────────────────────────────────────────────────

@flask_app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@flask_app.route("/", methods=["GET"])
def home():
    try:
        index_path = os.path.join(BASE_DIR, "index.html")
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        logger.error(f"Error serving index.html: {e}")
        return jsonify({"error": "An error occurred on the server."}), 500


@flask_app.route("/api/upload", methods=["POST"])
def upload_csv():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    if not file.filename.lower().endswith(".csv"):
        return jsonify({"error": "Only CSV files are supported"}), 400

    filename = secure_filename(file.filename)
    if not filename:
        return jsonify({"error": "Invalid filename"}), 400

    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        df = pd.read_csv(filepath)
        # Reset previous session, then build fresh agent for new file
        agent.reset_session()
        agent.build_agent(df)
        agent.set_filename(filename)

        return jsonify({
            "message":  "CSV uploaded and agent ready!",
            "filename": filename,
            "shape":    list(df.shape),
            "columns":  list(df.columns),
            "preview":  df.head(5).to_dict(orient="records"),
        })
    except Exception as e:
        logger.error(f"Error processing upload: {e}")
        return jsonify({"error": "An error occurred while processing the CSV file."}), 500


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
        logger.error(f"Error running chat query: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500


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
    port = int(os.environ.get("PORT", 8000))
    print(f"[*] Starting CSV AI Agent API on http://0.0.0.0:{port}")
    flask_app.run(host="0.0.0.0", port=port, debug=False)
