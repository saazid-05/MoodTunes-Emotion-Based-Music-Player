"""Main GUI for Emotion-Based Music Recommendation System."""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import cv2
from PIL import Image, ImageTk

from emotion_detector import EmotionDetector
from music_player import MusicPlayer
from music_mapper import get_playlist, ensure_music_dirs
from database import init_db, log_session, get_history

# ── Emotion color palette ──────────────────────────────────────────────────────
EMOTION_COLORS = {
    "happy":     "#FFD700",
    "sad":       "#6495ED",
    "angry":     "#FF4500",
    "surprised": "#FF69B4",
    "neutral":   "#90EE90",
    "fear":      "#9370DB",
    "disgust":   "#8B4513",
}
BG_COLOR   = "#1a1a2e"
CARD_COLOR = "#16213e"
TEXT_COLOR = "#e0e0e0"
ACCENT     = "#0f3460"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Emotion-Based Music Player")
        self.geometry("1100x750")
        self.configure(bg=BG_COLOR)
        self.resizable(True, True)

        ensure_music_dirs()
        init_db()

        self.player   = MusicPlayer(on_track_change=self._on_track_change)
        self.detector = EmotionDetector(on_emotion_detected=self._on_emotion)
        self.current_emotion = tk.StringVar(value="Detecting...")
        self.current_song    = tk.StringVar(value="No song loaded")
        self.status_msg      = tk.StringVar(value="Press 'Start Camera' to begin")
        self._camera_running = False

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── UI Construction ────────────────────────────────────────────────────────

    def _build_ui(self):
        # Left panel: camera feed
        left = tk.Frame(self, bg=BG_COLOR, width=480)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        left.pack_propagate(False)

        tk.Label(left, text="Emotion-Based Music Player", bg=BG_COLOR, fg=TEXT_COLOR,
                 font=("Helvetica", 13, "bold")).pack(pady=(5, 3))

        # Button at the TOP so it's always visible
        self.cam_btn = tk.Button(
            left, text="▶  Start Camera", command=self._toggle_camera,
            bg="#28a745", fg="white", font=("Helvetica", 12, "bold"),
            relief="flat", padx=20, pady=8, cursor="hand2", width=22
        )
        self.cam_btn.pack(pady=8)

        self.emotion_badge = tk.Label(
            left, textvariable=self.current_emotion,
            bg=EMOTION_COLORS["neutral"], fg="#000",
            font=("Helvetica", 14, "bold"), width=22, relief="flat", pady=5
        )
        self.emotion_badge.pack(pady=4)

        tk.Label(left, text="Live Camera Feed", bg=BG_COLOR, fg="#aaa",
                 font=("Helvetica", 10)).pack()

        self.cam_label = tk.Label(left, bg="#111111", width=460, height=300,
                                  relief="sunken")
        self.cam_label.pack(pady=5)

        # Right panel: player + history
        right = tk.Frame(self, bg=BG_COLOR)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self._build_player_card(right)
        self._build_history(right)

        # Status bar
        tk.Label(self, textvariable=self.status_msg, bg=ACCENT, fg=TEXT_COLOR,
                 font=("Helvetica", 9), anchor="w", padx=8).pack(
            side=tk.BOTTOM, fill=tk.X)

    def _build_player_card(self, parent):
        card = tk.Frame(parent, bg=CARD_COLOR, bd=0, relief="flat")
        card.pack(fill=tk.X, pady=(0, 10), ipady=10, ipadx=10)

        tk.Label(card, text="Now Playing", bg=CARD_COLOR, fg="#aaa",
                 font=("Helvetica", 10)).pack(pady=(10, 2))

        tk.Label(card, textvariable=self.current_song, bg=CARD_COLOR,
                 fg=TEXT_COLOR, font=("Helvetica", 13, "bold"),
                 wraplength=500).pack(pady=4)

        # Volume
        vol_frame = tk.Frame(card, bg=CARD_COLOR)
        vol_frame.pack(pady=6)
        tk.Label(vol_frame, text="🔊", bg=CARD_COLOR, fg=TEXT_COLOR,
                 font=("Helvetica", 12)).pack(side=tk.LEFT, padx=4)
        self.vol_slider = ttk.Scale(
            vol_frame, from_=0, to=1, orient=tk.HORIZONTAL, length=200,
            command=lambda v: self.player.set_volume(float(v))
        )
        self.vol_slider.set(1.0)
        self.vol_slider.pack(side=tk.LEFT)

        # Manual emotion selector
        sel_frame = tk.Frame(card, bg=CARD_COLOR)
        sel_frame.pack(pady=(4, 0))
        tk.Label(sel_frame, text="Play mood:", bg=CARD_COLOR, fg="#aaa",
                 font=("Helvetica", 10)).pack(side=tk.LEFT, padx=(0, 6))
        self.mood_var = tk.StringVar(value="neutral")
        mood_menu = ttk.Combobox(sel_frame, textvariable=self.mood_var,
                                 values=["happy", "sad", "angry", "surprised", "neutral"],
                                 state="readonly", width=12)
        mood_menu.pack(side=tk.LEFT, padx=4)
        tk.Button(sel_frame, text="▶ Play", command=self._manual_play,
                  bg="#28a745", fg="white", font=("Helvetica", 10, "bold"),
                  relief="flat", padx=10, pady=3, cursor="hand2").pack(side=tk.LEFT, padx=6)

        # Controls
        ctrl = tk.Frame(card, bg=CARD_COLOR)
        ctrl.pack(pady=8)
        for text, cmd in [("⏮", self.player.previous),
                          ("⏯", self.player.play_pause),
                          ("⏭", self.player.next)]:
            tk.Button(ctrl, text=text, command=cmd,
                      bg=ACCENT, fg="white", font=("Helvetica", 16),
                      relief="flat", width=4, cursor="hand2").pack(
                side=tk.LEFT, padx=6)

    def _build_history(self, parent):
        tk.Label(parent, text="Session History", bg=BG_COLOR, fg=TEXT_COLOR,
                 font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(4, 2))

        cols = ("Time", "Emotion", "Song")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings", height=12)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=CARD_COLOR, foreground=TEXT_COLOR,
                        fieldbackground=CARD_COLOR, rowheight=24)
        style.configure("Treeview.Heading", background=ACCENT, foreground="white")

        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=170 if col == "Song" else 130)

        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)

        self._refresh_history()

    # ── Event Handlers ─────────────────────────────────────────────────────────

    def _toggle_camera(self):
        if not self._camera_running:
            try:
                self.detector.start()
                self._camera_running = True
                self.cam_btn.config(text="⏹  Stop Camera", bg="#dc3545")
                self.status_msg.set("Camera active — detecting emotions...")
                self._update_frame()
            except RuntimeError as e:
                messagebox.showerror("Camera Error", str(e))
        else:
            self._stop_camera()

    def _update_frame(self):
        """Poll the detector for the latest frame and update the camera label."""
        if not self._camera_running:
            return
        frame = self.detector.get_frame()
        if frame is not None:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb).resize((460, 300))
            photo = ImageTk.PhotoImage(img)
            self.cam_label.configure(image=photo)
            self.cam_label.image = photo  # keep reference
        self.after(33, self._update_frame)  # ~30 fps

    def _manual_play(self):
        emotion = self.mood_var.get()
        playlist = get_playlist(emotion)
        if playlist:
            self.player.load_playlist(playlist)
            self.current_emotion.set(emotion.upper())
            self.emotion_badge.configure(bg=EMOTION_COLORS.get(emotion, "#90EE90"))
            log_session(emotion, playlist[0])
            self.after(0, self._refresh_history)
            self.status_msg.set(f"Manually playing {len(playlist)} songs for: {emotion.upper()}")
        else:
            self.status_msg.set(f"No songs found in music/{emotion}/")

    def _on_emotion(self, emotion: str, frame):
        """Called from detector thread when emotion changes — stops camera and plays music."""
        self.current_emotion.set(emotion.upper())
        color = EMOTION_COLORS.get(emotion, "#90EE90")
        self.emotion_badge.configure(bg=color)
        self.status_msg.set(f"Emotion detected: {emotion.upper()} — stopping camera...")

        # Stop camera automatically after emotion is detected
        self.after(0, self._stop_camera)

        playlist = get_playlist(emotion)
        if playlist:
            self.player.load_playlist(playlist)
            log_session(emotion, playlist[0])
            self.after(0, self._refresh_history)
            self.status_msg.set(f"Mood: {emotion.upper()} — Now playing {len(playlist)} songs")
        else:
            self.status_msg.set(
                f"No songs found for '{emotion}'. Add .wav files to music/{emotion}/")

    def _stop_camera(self):
        """Stop the camera feed and update button state."""
        if self._camera_running:
            self.detector.stop()
            self._camera_running = False
            self.cam_btn.config(text="▶  Start Camera", bg="#28a745")

    def _on_track_change(self, song_name: str):
        self.current_song.set(song_name)

    def _refresh_history(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for ts, emotion, song in get_history():
            time_str = ts[11:19]  # HH:MM:SS
            self.tree.insert("", 0, values=(time_str, emotion, song or "—"))

    def _on_close(self):
        self.detector.stop()
        self.player.stop()
        self.destroy()
