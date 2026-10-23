from flask import Flask, request, jsonify
from agent import run_agent
from offline import try_offline

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "success",
        "message": "Laptop Agent API is running!"
    })

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    command = data.get("message", "").strip()

    if not command:
        return jsonify({"error": "Message is required"}), 400

    try:
        reply = try_offline(command)

        if reply is None:
            reply = run_agent(command)

        return jsonify({"reply": str(reply)})

    except Exception as e:
        app.logger.exception("Agent execution failed")
        return jsonify({"error": "Failed to process message"}), 500
