"""
Generates emotionally distinct music samples for each mood folder.
Each emotion uses a different musical scale, tempo, and texture.
Run: python generate_music.py
"""

import wave, struct, math, os, random

SAMPLE_RATE = 44100
BASE = os.path.dirname(os.path.abspath(__file__))

# ── Music theory helpers ───────────────────────────────────────────────────────

def note(base_hz, semitones):
    return base_hz * (2 ** (semitones / 12))

# Scales (semitone intervals from root)
MAJOR       = [0, 2, 4, 5, 7, 9, 11, 12]
MINOR       = [0, 2, 3, 5, 7, 8, 10, 12]
PENTATONIC  = [0, 2, 4, 7, 9, 12]
DIMINISHED  = [0, 2, 3, 5, 6, 8, 9, 11]
WHOLE_TONE  = [0, 2, 4, 6, 8, 10, 12]

def build_scale(root_hz, intervals):
    return [note(root_hz, i) for i in intervals]


def sine(freq, t, harmonics=1):
    v = math.sin(2 * math.pi * freq * t)
    if harmonics >= 2:
        v += 0.4 * math.sin(2 * math.pi * freq * 2 * t)
    if harmonics >= 3:
        v += 0.2 * math.sin(2 * math.pi * freq * 3 * t)
    return v / (1 + 0.4 * (harmonics - 1) + 0.2 * max(0, harmonics - 2))


def envelope(i, total, attack=0.02, release=0.05):
    a = int(SAMPLE_RATE * attack)
    r = int(SAMPLE_RATE * release)
    if i < a:
        return i / a
    if i > total - r:
        return (total - i) / r
    return 1.0


def generate(scale, bpm, duration_sec, pattern, harmonics=2, vibrato=0.0, staccato=False):
    """Core generator — builds a melody from a scale + pattern."""
    samples = []
    beat = 60.0 / bpm
    note_dur = beat * 0.9 if not staccato else beat * 0.4
    silence  = beat - note_dur
    total    = SAMPLE_RATE * duration_sec
    t_global = 0.0

    idx = 0
    while len(samples) < total:
        freq = scale[pattern[idx % len(pattern)] % len(scale)]
        n_samples = int(SAMPLE_RATE * note_dur)
        s_samples = int(SAMPLE_RATE * silence)

        for i in range(n_samples):
            t = i / SAMPLE_RATE
            f = freq * (1 + vibrato * math.sin(2 * math.pi * 5 * (t_global + t)))
            v = sine(f, t, harmonics) * envelope(i, n_samples)
            samples.append(min(32767, max(-32767, int(v * 1.0 * 32767))))
            if len(samples) >= total:
                break

        for _ in range(s_samples):
            samples.append(0)
            if len(samples) >= total:
                break

        t_global += note_dur + silence
        idx += 1

    return samples[:total]


def write_wav(path, samples):
    # Write stereo by duplicating mono channel — louder on stereo speakers
    stereo = []
    for s in samples:
        stereo.append(s)
        stereo.append(s)
    with wave.open(path, "w") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(struct.pack(f"<{len(stereo)}h", *stereo))


# ── Emotion definitions ────────────────────────────────────────────────────────

def make_happy(path, seed):
    random.seed(seed)
    # C major, fast, bright, bouncy
    scale = build_scale(261.63, MAJOR)  # C4 major
    pattern = [0, 2, 4, 7, 4, 2, 0, 4, 2, 7, 5, 4]
    random.shuffle(pattern)
    s = generate(scale, bpm=138, duration_sec=12, pattern=pattern,
                 harmonics=2, vibrato=0.003, staccato=False)
    write_wav(path, s)


def make_sad(path, seed):
    random.seed(seed)
    # A minor, slow, soft, descending
    scale = build_scale(220.0, MINOR)   # A3 minor
    pattern = [7, 5, 4, 3, 2, 1, 0, 1, 2, 0, 3, 2]
    s = generate(scale, bpm=52, duration_sec=15, pattern=pattern,
                 harmonics=1, vibrato=0.006, staccato=False)
    write_wav(path, s)


def make_angry(path, seed):
    random.seed(seed)
    # D diminished, fast, harsh, aggressive
    scale = build_scale(146.83, DIMINISHED)  # D3 diminished
    pattern = [0, 0, 3, 0, 5, 3, 0, 6, 5, 3, 0, 0]
    s = generate(scale, bpm=185, duration_sec=10, pattern=pattern,
                 harmonics=3, vibrato=0.0, staccato=True)
    write_wav(path, s)


def make_neutral(path, seed):
    random.seed(seed)
    # G pentatonic, medium, calm, flowing
    scale = build_scale(196.0, PENTATONIC)  # G3 pentatonic
    pattern = [0, 1, 2, 3, 4, 3, 2, 1, 0, 2, 4, 2]
    s = generate(scale, bpm=80, duration_sec=14, pattern=pattern,
                 harmonics=2, vibrato=0.002, staccato=False)
    write_wav(path, s)


def make_surprised(path, seed):
    random.seed(seed)
    # E whole tone, fast, unpredictable, energetic
    scale = build_scale(164.81, WHOLE_TONE)  # E3 whole tone
    pattern = [0, 5, 1, 4, 2, 6, 3, 5, 0, 4, 2, 6]
    s = generate(scale, bpm=168, duration_sec=10, pattern=pattern,
                 harmonics=2, vibrato=0.008, staccato=True)
    write_wav(path, s)


# ── Main ───────────────────────────────────────────────────────────────────────

TRACKS = {
    "happy":     (make_happy,     3),
    "sad":       (make_sad,       3),
    "angry":     (make_angry,     3),
    "neutral":   (make_neutral,   3),
    "surprised": (make_surprised, 3),
}

def main():
    total = sum(count for _, count in TRACKS.values())
    done = 0
    for emotion, (fn, count) in TRACKS.items():
        folder = os.path.join(BASE, "music", emotion)
        os.makedirs(folder, exist_ok=True)

        # Remove old generated files
        for f in os.listdir(folder):
            if f.endswith(".wav"):
                os.remove(os.path.join(folder, f))

        for i in range(1, count + 1):
            done += 1
            filename = f"{emotion}_{i}.wav"
            dest = os.path.join(folder, filename)
            print(f"  [{done}/{total}] Generating {filename}  ({emotion})...")
            fn(dest, seed=i * 42)
            kb = os.path.getsize(dest) // 1024
            print(f"         ✓ {kb} KB")

    print("\nAll tracks ready. Run: python main.py")

if __name__ == "__main__":
    main()
