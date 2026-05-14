"""Real-time emotion detection — colored box + label + confidence %"""

import cv2
import numpy as np
import threading
import os
import urllib.request

EMOTIONS = ["neutral", "happy", "surprised", "sad", "angry", "disgust", "fear", "contempt"]

# Color per emotion (BGR)
EMOTION_COLORS = {
    "happy":     (0,   220,  0),
    "sad":       (220, 100,  0),
    "angry":     (0,   0,  220),
    "surprised": (0,   200, 255),
    "neutral":   (180, 180, 180),
    "fear":      (180, 0,   180),
    "disgust":   (0,   140, 100),
    "contempt":  (100, 100, 0),
}

MODEL_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model")
MODEL_PATH = os.path.join(MODEL_DIR, "emotion.onnx")
MODEL_URL  = "https://github.com/onnx/models/raw/main/validated/vision/body_analysis/emotion_ferplus/model/emotion-ferplus-8.onnx"
FACE_CASCADE = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"


def _download_model():
    os.makedirs(MODEL_DIR, exist_ok=True)
    if not os.path.exists(MODEL_PATH):
        print("[INFO] Downloading emotion model (~30MB)...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("[INFO] Model ready.")


class EmotionDetector:
    def __init__(self, on_emotion_detected=None):
        self.on_emotion_detected = on_emotion_detected
        self.cap             = None
        self.running         = False   # camera loop running
        self.detecting       = False   # actively looking for emotion
        self.current_emotion = ""
        self.current_frame   = None
        self.current_scores  = {}
        self._thread         = None
        self._lock           = threading.Lock()
        self._face_cascade   = cv2.CascadeClassifier(FACE_CASCADE)
        self._net            = None

    def _load_model(self):
        _download_model()
        try:
            self._net = cv2.dnn.readNetFromONNX(MODEL_PATH)
            print("[INFO] ONNX model loaded.")
        except Exception as e:
            print(f"[WARN] Model load failed: {e}")
            self._net = None

    def start_camera(self):
        """Start camera loop (keeps running until stop_camera)."""
        if self.running:
            return
        self._load_model()
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise RuntimeError("Cannot access webcam.")
        self.running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def start_detection(self):
        """Trigger one-shot emotion detection on the running camera."""
        self.detecting = True
        self.current_emotion = ""

    def stop_camera(self):
        self.running = False
        self.detecting = False
        if self.cap:
            self.cap.release()
            self.cap = None

    # Legacy compat
    def start(self):
        self.start_camera()
        self.start_detection()

    def stop(self):
        self.stop_camera()

    def get_frame(self):
        with self._lock:
            return self.current_frame

    def get_scores(self):
        with self._lock:
            return self.current_scores.copy()

    def _predict(self, gray_face):
        """Returns (emotion_str, scores_dict)"""
        if self._net is None:
            return "neutral", {e: (100.0 if e == "neutral" else 0.0) for e in EMOTIONS}
        try:
            blob = cv2.dnn.blobFromImage(
                cv2.resize(gray_face, (64, 64)), 1.0, (64, 64), (0, 0, 0), swapRB=False
            )
            self._net.setInput(blob)
            raw = self._net.forward()[0]
            e_x = np.exp(raw - np.max(raw))
            probs = e_x / e_x.sum()
            scores = {EMOTIONS[i]: round(float(probs[i]) * 100, 1) for i in range(len(EMOTIONS))}
            dominant = max(scores, key=scores.get)
            return dominant, scores
        except Exception as ex:
            print(f"[WARN] Predict error: {ex}")
            return "neutral", {}

    def _draw_box(self, frame, x, y, w, h, emotion, confidence):
        color = EMOTION_COLORS.get(emotion, (180, 180, 180))
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        label = f"{emotion.upper()}  {confidence:.0f}%"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.65, 2)
        cv2.rectangle(frame, (x, y - th - 10), (x + tw + 8, y), color, -1)
        cv2.putText(frame, label, (x + 4, y - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 2)

    def _loop(self):
        frame_count = 0
        # Accumulate votes for stable detection
        votes = []
        VOTE_NEEDED = 5  # need 5 consistent frames before triggering

        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                import time; time.sleep(0.02)
                continue

            frame_count += 1
            annotated = frame.copy()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Always detect faces and draw boxes
            if frame_count % 4 == 0:
                faces = self._face_cascade.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=5, minSize=(48, 48)
                )
                if len(faces) > 0:
                    x, y, w, h = faces[0]
                    face_roi = gray[y:y + h, x:x + w]
                    detected, scores = self._predict(face_roi)
                    confidence = scores.get(detected, 0)

                    self._draw_box(annotated, x, y, w, h, detected, confidence)

                    with self._lock:
                        self.current_scores = scores
                        self.current_emotion = detected

                    # Only fire callback when actively detecting
                    if self.detecting:
                        votes.append(detected)
                        if len(votes) >= VOTE_NEEDED:
                            # Pick most common emotion from votes
                            from collections import Counter
                            final = Counter(votes).most_common(1)[0][0]
                            votes.clear()
                            self.detecting = False
                            if self.on_emotion_detected:
                                self.on_emotion_detected(final, annotated, scores)
                else:
                    if self.detecting:
                        votes.clear()  # reset if face lost

            with self._lock:
                self.current_frame = annotated

            import time; time.sleep(0.03)
