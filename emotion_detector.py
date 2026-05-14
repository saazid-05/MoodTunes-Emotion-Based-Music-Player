"""
Downloads free royalty-free music from Pixabay into emotion folders.
Run once: python download_music.py
"""

import urllib.request
import os
import json
import time

# Free Pixabay music URLs (royalty-free, no API key needed for direct links)
# Manually curated direct MP3 links from pixabay.com/music
SONGS = {
    "happy": [
        ("happy_ukulele.mp3",    "https://cdn.pixabay.com/download/audio/2022/01/18/audio_d0c6ff1bab.mp3"),
        ("sunny_day.mp3",        "https://cdn.pixabay.com/download/audio/2022/03/15/audio_8cb749d577.mp3"),
        ("cheerful_pop.mp3",     "https://cdn.pixabay.com/download/audio/2021/11/25/audio_5b5b3b3b3b.mp3"),
    ],
    "sad": [
        ("sad_piano.mp3",        "https://cdn.pixabay.com/download/audio/2022/10/25/audio_946b4a8a4a.mp3"),
        ("melancholy.mp3",       "https://cdn.pixabay.com/download/audio/2022/08/02/audio_884fe92c21.mp3"),
    ],
    "angry": [
        ("intense_rock.mp3",     "https://cdn.pixabay.com/download/audio/2022/11/22/audio_febc508520.mp3"),
        ("dark_energy.mp3",      "https://cdn.pixabay.com/download/audio/2023/01/10/audio_8ea1ad5c7b.mp3"),
    ],
    "neutral": [
        ("ambient_calm.mp3",     "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3"),
        ("lofi_chill.mp3",       "https://cdn.pixabay.com/download/audio/2022/02/07/audio_d1718ab41b.mp3"),
    ],
    "surprised": [
        ("energetic_beat.mp3",   "https://cdn.pixabay.com/download/audio/2022/06/07/audio_b9b8e5d9e9.mp3"),
        ("upbeat_electronic.mp3","https://cdn.pixabay.com/download/audio/2021/08/09/audio_dc39bde808.mp3"),
    ],
}


def download():
    base = os.path.dirname(__file__)
    total = sum(len(v) for v in SONGS.values())
    done = 0

    for emotion, tracks in SONGS.items():
        folder = os.path.join(base, "music", emotion)
        os.makedirs(folder, exist_ok=True)

        for filename, url in tracks:
            dest = os.path.join(folder, filename)
            if os.path.exists(dest):
                print(f"  [skip] {filename} already exists")
                done += 1
                continue
            try:
                print(f"  [{done+1}/{total}] Downloading {filename}...")
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=15) as r, open(dest, "wb") as f:
                    f.write(r.read())
                size_kb = os.path.getsize(dest) // 1024
                print(f"         ✓ {filename} ({size_kb} KB)")
            except Exception as e:
                print(f"         ✗ Failed: {e}")
            done += 1
            time.sleep(0.5)

    print("\nDone. Run: python main.py")


if __name__ == "__main__":
    download()
