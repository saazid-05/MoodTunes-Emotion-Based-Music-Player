"""Flask web app for Emotion-Based Music Player."""

import os
import threading
import time
import cv2
import numpy as np
from flask import Flask, render_template, jsonify, send_file, Response, make_response, request

from emotion_detector import EmotionDetector
from music_mapper import get_playlist
from database import init_db, log_session

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"))
init_db()

# ── App state ──────────────────────────────────────────────────────────────────
state = {
    "emotion":    "none",
    "playlist":   [],
    "index":      0,
    "detecting":  False,
    "scores":     {},
    "last_frame": None,
}

EMOTION_GRADIENTS = {
    "happy":     "linear-gradient(135deg,#b8860b,#ffd700)",
    "sad":       "linear-gradient(135deg,#1a3a6a,#4a90d9)",
    "angry":     "linear-gradient(135deg,#6a0000,#e74c3c)",
    "surprised": "linear-gradient(135deg,#6a0040,#e63ab0)",
    "neutral":   "linear-gradient(135deg,#1a4a2a,#4ade80)",
    "fear":      "linear-gradient(135deg,#2a0a4a,#9b59b6)",
    "disgust":   "linear-gradient(135deg,#3a2a00,#c8a84b)",
    "contempt":  "linear-gradient(135deg,#2a2a2a,#888)",
    "none":      "linear-gradient(135deg,#1a1a2e,#16213e)",
}
EMOTION_EMOJI = {
    "happy":"😄","sad":"😢","angry":"😠","surprised":"😲",
    "neutral":"�","fear":"😨 ","disgust":"🤢","contempt":"😒","none":"🎵",
}

# ── Detector ───────────────────────────────────────────────────────────────────
detector = EmotionDetector()


def on_emotion(emotion, frame, scores=None):
    scores = scores or {}
    playlist = get_playlist(emotion)
    state["emotion"]    = emotion
    state["playlist"]   = playlist
    state["scores"]     = scores
    state["index"]      = 0
    state["detecting"]  = False
    state["last_frame"] = frame  # freeze this frame
    if playlist:
        log_session(emotion, playlist[0])
    print(f"[INFO] Emotion detected: {emotion} | Playlist: {len(playlist)} songs")
    # Stop camera after detection
    detector.stop_camera()


detector.on_emotion_detected = on_emotion

# ── Video stream ───────────────────────────────────────────────────────────────

def frame_generator():
    while True:
        frame = detector.get_frame()
        if frame is not None:
            _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" +
                   buf.tobytes() + b"\r\n")
        else:
            # Blank placeholder while camera not started
            blank = np.zeros((360, 480, 3), dtype=np.uint8)
            cv2.putText(blank, "Click 'Detect My Mood' to start", (40, 180),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (120, 120, 120), 1)
            _, buf = cv2.imencode(".jpg", blank)
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" +
                   buf.tobytes() + b"\r\n")
        time.sleep(0.033)  # ~30fps


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    resp = make_response(render_template("index.html"))
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp


@app.route("/snapshot")
def snapshot():
    """Return the last captured frame as a JPEG image."""
    frame = state.get("last_frame")
    if frame is None:
        blank = np.zeros((360, 480, 3), dtype=np.uint8)
        cv2.putText(blank, "No snapshot yet", (120, 180),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (120, 120, 120), 1)
        frame = blank
    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    from flask import send_file
    import io
    return send_file(io.BytesIO(buf.tobytes()), mimetype="image/jpeg")


@app.route("/video_feed")
def video_feed():
    return Response(frame_generator(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/start_camera", methods=["POST"])
def start_camera():
    try:
        detector.start_camera()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})


@app.route("/stop_camera", methods=["POST"])
def stop_camera():
    detector.stop_camera()
    return jsonify({"status": "ok"})


@app.route("/detect", methods=["POST"])
def detect():
    if state["detecting"]:
        return jsonify({"status": "already detecting"})
    if not detector.running:
        try:
            detector.start_camera()
        except Exception as e:
            return jsonify({"status": "error", "msg": str(e)})
    state["detecting"] = True
    state["emotion"]   = "none"
    detector.start_detection()
    return jsonify({"status": "started"})


@app.route("/status")
def status():
    playlist = state["playlist"]
    idx      = state["index"]
    song     = os.path.basename(playlist[idx]) if playlist else ""
    return jsonify({
        "emotion":   state["emotion"],
        "detecting": state["detecting"],
        "song":      song,
        "total":     len(playlist),
        "index":     idx,
        "gradient":  EMOTION_GRADIENTS.get(state["emotion"], EMOTION_GRADIENTS["none"]),
        "emoji":     EMOTION_EMOJI.get(state["emotion"], "🎵"),
        "scores":    state["scores"],
        "playlist":  [os.path.basename(p) for p in playlist],
    })


@app.route("/song")
def song():
    playlist = state["playlist"]
    if not playlist:
        return "No song", 404
    path = playlist[state["index"]]
    if not os.path.exists(path):
        return "File not found", 404
    mime = "audio/mpeg" if path.lower().endswith(".mp3") else "audio/wav"
    return send_file(path, mimetype=mime)


@app.route("/next", methods=["POST"])
def next_song():
    if state["playlist"]:
        state["index"] = (state["index"] + 1) % len(state["playlist"])
    idx = state["index"]
    song = os.path.basename(state["playlist"][idx]) if state["playlist"] else ""
    return jsonify({"index": idx, "song": song})


@app.route("/prev", methods=["POST"])
def prev_song():
    if state["playlist"]:
        state["index"] = (state["index"] - 1) % len(state["playlist"])
    idx = state["index"]
    song = os.path.basename(state["playlist"][idx]) if state["playlist"] else ""
    return jsonify({"index": idx, "song": song})


@app.route("/browse")
def browse():
    """Return all songs grouped by emotion folder."""
    from music_mapper import EMOTION_FOLDERS, SUPPORTED_FORMATS
    result = {}
    seen = set()
    for emotion, folder in EMOTION_FOLDERS.items():
        if folder in seen:
            continue
        seen.add(folder)
        if not os.path.isdir(folder):
            continue
        files = [f for f in os.listdir(folder) if f.lower().endswith(SUPPORTED_FORMATS)]
        if files:
            result[emotion] = sorted(files)
    return jsonify(result)


@app.route("/play_file", methods=["POST"])
def play_file():
    """Play a specific file by emotion + filename (manual selection)."""
    data     = request.get_json()
    emotion  = data.get("emotion", "")
    filename = data.get("file", "")
    from music_mapper import EMOTION_FOLDERS
    folder = EMOTION_FOLDERS.get(emotion)
    if not folder:
        return jsonify({"status": "error", "msg": "Unknown emotion"}), 400
    path = os.path.join(folder, filename)
    if not os.path.exists(path):
        return jsonify({"status": "error", "msg": "File not found"}), 404

    # Build playlist from that folder, put selected song first
    from music_mapper import SUPPORTED_FORMATS
    all_files = sorted([
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith(SUPPORTED_FORMATS)
    ])
    # Rotate so selected song is at index 0
    try:
        sel_idx = [os.path.basename(p) for p in all_files].index(filename)
        all_files = all_files[sel_idx:] + all_files[:sel_idx]
    except ValueError:
        pass

    state["playlist"] = all_files
    state["index"]    = 0
    state["emotion"]  = emotion
    state["scores"]   = {}
    log_session(emotion, path)
    return jsonify({"status": "ok", "song": filename, "total": len(all_files)})


if __name__ == "__main__":
    app.run(debug=False, port=8080, threaded=True)
