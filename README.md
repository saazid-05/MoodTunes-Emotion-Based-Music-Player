# MoodTunes: Emotion-Based Music Player

MoodTunes is an innovative music player that detects your emotions through your webcam and recommends music that matches your current mood. It uses machine learning for real-time emotion recognition and provides both a desktop GUI and a web interface.

## Features

- **Real-time Emotion Detection**: Uses computer vision and a pre-trained ONNX model to detect emotions from facial expressions
- **Emotion-Based Music Mapping**: Automatically selects and plays music from emotion-specific playlists
- **Dual Interfaces**: Choose between a desktop GUI application or a modern web interface
- **Session Logging**: Tracks your emotional states and music preferences over time
- **Supported Emotions**: Happy, Sad, Angry, Surprised, Neutral, Fear, Disgust, Contempt
- **Multiple Audio Formats**: Supports MP3, WAV, OGG, and FLAC files

## Requirements

- Python 3.8 or higher
- Webcam for emotion detection
- Operating System: Windows, macOS, or Linux

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Desktop GUI Application

Run the desktop application:

```bash
python main.py
```

This launches a Tkinter-based GUI that provides full control over the music player.

### Web Interface

Run the web application:

```bash
python app.py
```

Then open your browser and navigate to `http://localhost:5000` to access the modern web interface.

## Music Setup

1. Create emotion-specific folders in the `music/` directory (automatically created if they don't exist)
2. Add your music files to the corresponding emotion folders:
   - `music/happy/` - Upbeat, cheerful songs
   - `music/sad/` - Melancholic, soothing songs
   - `music/angry/` - Energetic, intense songs
   - `music/surprised/` - Exciting, adventurous songs
   - `music/neutral/` - Calm, balanced songs

Note: Fear maps to sad music, Disgust and Contempt map to angry music.

## How It Works

1. **Emotion Detection**: The system captures video from your webcam and analyzes facial expressions using a deep learning model
2. **Music Selection**: Based on the detected emotion, it selects a random song from the appropriate emotion folder
3. **Playback**: The selected music plays automatically, adapting to your changing emotions
4. **Logging**: Your emotional journey and music preferences are logged in a local database

## Project Structure

```
emotion-music-player/
├── app.py                 # Flask web application
├── main.py               # Entry point for GUI application
├── gui.py                # Desktop GUI implementation
├── emotion_detector.py   # Emotion detection logic
├── music_player.py       # Music playback functionality
├── music_mapper.py       # Emotion-to-music mapping
├── database.py           # Session logging and history
├── download_music.py     # Music download utilities
├── generate_music.py     # Music generation (if applicable)
├── requirements.txt      # Python dependencies
├── model/
│   └── emotion.onnx      # Pre-trained emotion detection model
├── music/                # Emotion-specific music folders
│   ├── happy/
│   ├── sad/
│   ├── angry/
│   ├── surprised/
│   └── neutral/
└── templates/
    └── index.html        # Web interface template
```

## Dependencies

- Flask: Web framework
- OpenCV: Computer vision and video processing
- NumPy: Numerical computing
- Pillow: Image processing
- Tkinter: GUI framework (built-in with Python)

## Contributing

Feel free to contribute to the project by:
- Adding support for more emotions
- Improving the emotion detection accuracy
- Enhancing the user interface
- Adding more audio formats or streaming capabilities

## License

This project is open-source. Please check the license file for more details.

## Disclaimer

This application requires camera access for emotion detection. Please ensure you have appropriate permissions and privacy considerations in mind when using this software.
