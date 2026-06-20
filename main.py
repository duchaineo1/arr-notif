import json
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


def send_ntfy(message, title, tags):
    response = requests.post(
        NTFY_TOPIC_URL,
        data=message.encode('utf-8'),
        headers={
            "Title": title,
            "Tags": tags,
            "Priority": "3",
        }
    )
    if response.status_code != 200:
        log.error("ntfy returned %d: %s", response.status_code, response.text)
        return False
    return True


@app.route('/sonarr', methods=['POST'])
def sonarr():
    log.info("POST /sonarr from %s", request.remote_addr)
    data = request.get_json()

    if not data:
        log.warning("Rejected: empty or non-JSON body")
        return jsonify({"error": "Invalid payload"}), 400

    event_type = data.get("eventType", "Unknown")
    log.info("Event type: %s", event_type)

    if event_type == "Test":
        log.info("Test payload:\n%s", json.dumps(data, indent=2))
        return jsonify({"status": "Test received"}), 200

    if "series" not in data or "episodes" not in data:
        log.warning("Rejected: missing series or episodes fields")
        return jsonify({"error": "Invalid payload"}), 400

    series = data["series"]
    episodes = data["episodes"]
    log.info("Series: %s, episodes: %d", series.get("title", "Unknown"), len(episodes))

    message_lines = [
        f"📺 {event_type}",
        f"Series: {series.get('title', 'Unknown')}",
        "",
        "Episodes:",
    ]
    for ep in episodes:
        message_lines.append(
            f" - S{ep['seasonNumber']:02}E{ep['episodeNumber']:02}: {ep['title']}"
        )

    if not send_ntfy("\n".join(message_lines), "New Episode", "tv,alert"):
        return jsonify({"error": "Failed to send notification"}), 500

    log.info("Notification sent")
    return jsonify({"status": "Notification sent"}), 200


@app.route('/radarr', methods=['POST'])
def radarr():
    log.info("POST /radarr from %s", request.remote_addr)
    data = request.get_json()

    if not data:
        log.warning("Rejected: empty or non-JSON body")
        return jsonify({"error": "Invalid payload"}), 400

    event_type = data.get("eventType", "Unknown")
    log.info("Event type: %s", event_type)

    if event_type == "Test":
        log.info("Test payload:\n%s", json.dumps(data, indent=2))
        return jsonify({"status": "Test received"}), 200

    movie = data.get("movie")
    if not movie:
        log.warning("Rejected: missing movie field")
        return jsonify({"error": "Invalid payload"}), 400

    release = data.get("release", {})
    title = movie.get("title", "Unknown")
    year = movie.get("year", "")
    quality = release.get("quality", "Unknown")
    release_group = release.get("releaseGroup", "")
    log.info("Movie: %s (%s), quality: %s", title, year, quality)

    message_lines = [
        f"🎬 {event_type}",
        f"Movie: {title} ({year})",
        f"Quality: {quality}",
    ]
    if release_group:
        message_lines.append(f"Release Group: {release_group}")

    if not send_ntfy("\n".join(message_lines), "New Movie", "movie,alert"):
        return jsonify({"error": "Failed to send notification"}), 500

    log.info("Notification sent")
    return jsonify({"status": "Notification sent"}), 200


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
