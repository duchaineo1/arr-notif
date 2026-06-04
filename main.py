import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

NTFY_TOPIC_URL = os.environ.get("NTFY_TOPIC_URL", "https://ntfy.sh/jellyfin-new-item")

@app.route('/notify', methods=['POST'])
def notify():
    data = request.get_json()

    # Validate the basic structure
    if not data or "series" not in data or "episodes" not in data:
        return jsonify({"error": "Invalid payload"}), 400

    series = data["series"]
    episodes = data["episodes"]
    event_type = data.get("eventType", "Unknown")

    # Build a human-readable message
    message_lines = [
        f"📺 Event Type: {event_type}",
        f"Series: {series.get('title', 'Unknown')}",
        f"Path: {series.get('path', 'N/A')}",
        f"TVDB ID: {series.get('tvdbId', 'N/A')}",
        f"Type: {series.get('type', 'N/A')}",
        "",
        "Episodes:"
    ]

    for ep in episodes:
        message_lines.append(f" - S{ep['seasonNumber']:02}E{ep['episodeNumber']:02}: {ep['title']} (ID: {ep['id']})")

    message = "\n".join(message_lines)

    # Send to ntfy
    response = requests.post(
        NTFY_TOPIC_URL,
        data=message.encode('utf-8'),
        headers={
            "Title": "New Series Event",
            "Tags": "tv,alert",
            "Priority": "3"
        }
    )

    if response.status_code != 200:
        return jsonify({"error": "Failed to send notification", "details": response.text}), 500

    return jsonify({"status": "Notification sent"}), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)


