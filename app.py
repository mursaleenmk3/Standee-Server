from flask import Flask, request, jsonify, send_file
from pathlib import Path
import os
import subprocess
import time

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
SETTINGS_DIR = BASE_DIR / "settings"
AUDIO_DIR = SETTINGS_DIR / "greeting_audio"
BACKGROUND_DIR = SETTINGS_DIR / "background_music"

TTS_FILE = SETTINGS_DIR / "greeting.txt"
MODE_FILE = SETTINGS_DIR / "mode.txt"
AUDIO_MODE_FILE = SETTINGS_DIR / "audio_mode.txt"
BG_FLAG_FILE = SETTINGS_DIR / "background_music_flag.txt"
STATUS_FILE = SETTINGS_DIR / "detection_status.txt"

# Create folders
for d in [SETTINGS_DIR, AUDIO_DIR, BACKGROUND_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Create empty files if they don't exist
for f in [TTS_FILE, MODE_FILE, AUDIO_MODE_FILE, BG_FLAG_FILE, STATUS_FILE]:
    if not f.exists():
        f.write_text("")


def write_file(path, data):
    with open(path, "w") as f:
        f.write(data)

def read_file(path, default=""):
    return open(path).read().strip() if path.exists() else default

@app.route('/')
def home():
    return jsonify({"status": "Flask Server Running"})

# Optional: global or file-based flag
should_start = False

@app.route('/start', methods=['POST'])
def set_start_flag():
    global should_start
    should_start = True
    return jsonify({"success": True, "message": "Start signal received."})

@app.route('/check-start', methods=['GET'])
def check_start_flag():
    global should_start
    return jsonify({"start": should_start})


@app.route('/stop', methods=['POST'])
def stop_detection():
    write_file(STATUS_FILE, "off")
    return jsonify({"message": "Detection stopped"})

@app.route('/set-message', methods=['POST'])
def set_message():
    data = request.json
    msg = data.get("message", "")
    write_file(TTS_FILE, msg)
    return jsonify({"message": "TTS message set"})

@app.route('/set-mode', methods=['POST'])
def set_mode():
    data = request.json
    mode = data.get("mode", "").lower()
    if mode in ["tts", "mp3"]:
        write_file(MODE_FILE, mode)
        return jsonify({"message": f"Mode set to {mode}"})
    return jsonify({"error": "Invalid mode"}), 400

@app.route('/upload-audio', methods=['POST'])
def upload_audio():
    file = request.files.get("file")
    if file:
        path = AUDIO_DIR / file.filename
        file.save(path)
        return jsonify({"message": "Greeting audio uploaded"})
    return jsonify({"error": "No file uploaded"}), 400

@app.route('/upload-background', methods=['POST'])
def upload_background():
    file = request.files.get("file")
    if file:
        path = BACKGROUND_DIR / file.filename
        file.save(path)
        return jsonify({"message": "Background music uploaded"})
    return jsonify({"error": "No file uploaded"}), 400

@app.route('/background-music-flag', methods=['POST'])
def toggle_background_music():
    data = request.json
    enabled = str(data.get("enabled", "false")).lower()
    write_file(BG_FLAG_FILE, "true" if enabled == "true" else "false")
    return jsonify({"message": f"Background music {'enabled' if enabled == 'true' else 'disabled'}"})

@app.route('/set-audio-mode', methods=['POST'])
def set_audio_mode():
    data = request.json
    mode = data.get("mode", "").lower()
    if mode in ["wired", "bluetooth"]:
        write_file(AUDIO_MODE_FILE, mode)
        return jsonify({"message": f"Audio output set to {mode}"})
    return jsonify({"error": "Invalid audio mode"}), 400

@app.route('/next', methods=['POST'])
def next_track():
    return jsonify({"message": "Next track requested"})  # client handles actual logic

@app.route('/previous', methods=['POST'])
def previous_track():
    return jsonify({"message": "Previous track requested"})  # client handles actual logic

@app.route('/play-tts', methods=['POST'])
def play_tts():
    message = read_file(TTS_FILE, "Hello! Welcome.")
    # You can implement real-time TTS here if needed
    return jsonify({"message": message})

@app.route('/detection-status', methods=['GET'])
def get_detection_status():
    return jsonify({"status": read_file(STATUS_FILE, "off")})

@app.route('/sync-files', methods=['GET'])
def sync_files():
    return jsonify({
        "detection_status": read_file(STATUS_FILE, "off"),
        "message": read_file(TTS_FILE, "Hello! Welcome."),
        "mode": read_file(MODE_FILE, "tts"),
        "audio_mode": read_file(AUDIO_MODE_FILE, "wired"),
        "background_music_flag": read_file(BG_FLAG_FILE, "false")
    })

if __name__ == '__main__':
    app.run()
