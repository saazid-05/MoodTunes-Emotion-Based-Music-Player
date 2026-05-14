"""Maps detected emotions to music folders and manages playlists."""

import os
import random

# Base directory = folder where this file lives
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

EMOTION_FOLDERS = {
    "happy":     os.path.join(BASE_DIR, "music", "happy"),
    "sad":       os.path.join(BASE_DIR, "music", "sad"),
    "angry":     os.path.join(BASE_DIR, "music", "angry"),
    "surprised": os.path.join(BASE_DIR, "music", "surprised"),
    "neutral":   os.path.join(BASE_DIR, "music", "neutral"),
    "fear":      os.path.join(BASE_DIR, "music", "sad"),
    "disgust":   os.path.join(BASE_DIR, "music", "angry"),
    "contempt":  os.path.join(BASE_DIR, "music", "angry"),
}

SUPPORTED_FORMATS = (".mp3", ".wav", ".ogg", ".flac")


def get_playlist(emotion: str) -> list[str]:
    """Return a shuffled list of absolute song paths for the given emotion."""
    emotion = emotion.lower()
    folder = EMOTION_FOLDERS.get(emotion, EMOTION_FOLDERS["neutral"])

    if not os.path.isdir(folder):
        os.makedirs(folder, exist_ok=True)
        return []

    songs = [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith(SUPPORTED_FORMATS)
    ]
    random.shuffle(songs)
    return songs


def ensure_music_dirs():
    """Create all emotion music directories if they don't exist."""
    for folder in set(EMOTION_FOLDERS.values()):
        os.makedirs(folder, exist_ok=True)
