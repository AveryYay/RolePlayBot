from flask import Flask, request, jsonify
from camel.agents import ChatAgent
import uuid
import os

app = Flask(__name__)
agent = ChatAgent(
    system_message=(
        "You are summarizing a scene presented from the player's point of view, "
        "so the original dialogue and narration may use 'You' to refer to "
        "the player."
        "However, in your summary, do not use 'You' or 'I' when narrating. "
        "Instead, refer to 'the player' or use character names. "
        "You may retain 'You' or 'I' only when quoting lines of dialogue "
        "exactly as spoken. "
        "Make sure to clearly capture the player's choices and Sheldon's "
        "responses, as these are the most important aspects of the interaction."
    )
)

@app.route("/add_interaction", methods=["POST"])
def add_interaction():
    data = request.get_json()
    text = data.get("text")
    if not text:
        return jsonify({"error": "Missing 'text' field in JSON."}), 400

    try:
        os.makedirs("./pending_interactions", exist_ok=True)
        file_id = str(uuid.uuid4())
        with open(f"./pending_interactions/{file_id}.txt", "w",
                  encoding="utf-8") as f:
            summary = agent.step(text).msgs[0].content
            f.write(summary)
        return jsonify({"message": "Interaction saved to file."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5002)
