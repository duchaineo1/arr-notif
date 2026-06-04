import logging
import os
from flask import Flask, request, jsonify
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

app = Flask(__name__)

NTFY_TOPIC_URL = os.environ.get("NTFY_TOPIC_URL")


@app.route('/notify', methods=['POST'])
def notify():
    log.info("POST /notify from %s", request.remote_addr)
    data = request.get_json()

    if not data:
        log.warning("Rejected request: empty or non-JSON body")
        return jsonify({"error": "Invalid payload"}), 400

    event_type = data.get("eventType", "Unknown")
    log.info("Event type: %s", event_type)

    if event_type == "Test":
        log.info("Test event received, returning OK")
        return jsonify({"status": "Test received"}), 200

    if "series" not in data or "episodes" not in data:
        log.warning("Rejected request: missing series or episodes fields")
        return jsonify({"error": "Invalid payload"}), 400

    series = data["series"]
    episodes = data["episodes"]
    log.info("Series: %s, episodes: %d", series.get("title", "Unknown"), len(episodes))

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

    log.info("Sending notification to ntfy")
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
        log.error("ntfy returned %d: %s", response.status_code, response.text)
        return jsonify({"error": "Failed to send notification", "details": response.text}), 500

    log.info("Notification sent successfully")
    return jsonify({"status": "Notification sent"}), 200


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
