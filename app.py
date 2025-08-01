from flask import Flask, request, jsonify, send_file
from pathlib import Path
import os
import logging
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Logging setup
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("render-app")

app = Flask(__name__)
CORS(app)

# Directory setup
BASE_DIR = Path(__file__).resolve().parent
SETTINGS_DIR = BASE_DIR / "settings"
AUDIO_DIR = SETTINGS_DIR / "greeting_audio"
BACKGROUND_DIR = SETTINGS_DIR / "background_music"

TTS_FILE = SETTINGS_DIR / "greeting.txt"
MODE_FILE = SETTINGS_DIR / "mode.txt"
AUDIO_MODE_FILE = SETTINGS_DIR / "audio_mode.txt"
BG_FLAG_FILE = SETTINGS_DIR / "background_music_flag.txt"
STATUS_FILE = SETTINGS_DIR / "detection_status.txt"
MESSAGE_FILE = SETTINGS_DIR / "latest_message.txt"

# Create folders
for d in [SETTINGS_DIR, AUDIO_DIR, BACKGROUND_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Create empty files if they don't exist
for f in [TTS_FILE, MODE_FILE, AUDIO_MODE_FILE, BG_FLAG_FILE, STATUS_FILE, MESSAGE_FILE]:
    if not f.exists():
        f.write_text("")

# Helper functions
def write_file(path, data):
    with open(path, "w") as f:
        f.write(data)

def read_file(path, default=""):
    return open(path).read().strip() if path.exists() else default

def response(success, message, status):
    return jsonify({"success": success, "message": message}), status

# Routes

@app.route('/')
def home():
    return jsonify({"status": "Flask Server Running"})

# Global flag for /start-check
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
    try:
        msg = request.data.decode('utf-8').strip()
        if not msg:
            return response(False, "Empty message", 400)
        MESSAGE_FILE.write_text(msg)
        return response(True, "Message saved", 200)
    except Exception as e:
        return response(False, f"Save error: {e}", 500)

@app.route('/get-message', methods=['GET'])
def get_message():
    try:
        if MESSAGE_FILE.exists():
            return jsonify({"message": MESSAGE_FILE.read_text().strip()})
        else:
            return jsonify({"message": ""})
    except Exception as e:
        return response(False, f"Error reading message: {e}", 500)

@app.route('/set-mode', methods=['POST'])
def set_mode():
    try:
        mode = request.data.decode('utf-8').strip()
        if not mode:
            return "Empty mode", 400
        MODE_FILE.write_text(mode)
        return "Mode saved", 200
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/get-mode', methods=['GET'])
def get_mode():
    try:
        if not MODE_FILE.exists():
            return "No mode set", 404
        return MODE_FILE.read_text().strip(), 200
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/upload-audio', methods=['POST'])
def upload_audio():
    file = request.files.get("file")
    if file:
        path = AUDIO_DIR / secure_filename(file.filename)
        file.save(path)
        log.info(f"Greeting audio uploaded: {path}")
        return jsonify({"message": "Greeting audio uploaded"})
    return jsonify({"error": "No file uploaded"}), 400

@app.route('/start-bg-music', methods=['POST'])
def start_bg_music():
    try:
        mode = request.data.decode('utf-8').strip()
        BG_FLAG_FILE.write_text(mode)
        return jsonify({'success': True, 'message': 'Background music flag enabled'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f"Start music flag error: {str(e)}"}), 500

@app.route('/get-bg-music', methods=['GET'])
def get_bg_music_status():
    try:
        if not BG_FLAG_FILE.exists():
            return jsonify({"mode": None, "message": "No mode set"}), 404
        mode = BG_FLAG_FILE.read_text().strip()
        return jsonify({"mode": mode}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/upload-background', methods=['POST'])
def upload_background():
    file = request.files.get("file")
    if file:
        path = BACKGROUND_DIR / secure_filename(file.filename)
        file.save(path)
        log.info(f"Background music uploaded: {path}")
        return jsonify({"message": "Background music uploaded"})
    return jsonify({"error": "No file uploaded"}), 400

@app.route('/background-music-flag', methods=['POST'])
def toggle_background_music():
    try:
        data = request.get_json(force=True)
        enabled = str(data.get("enabled", "false")).lower()
        write_file(BG_FLAG_FILE, "true" if enabled == "true" else "false")
        return jsonify({"message": f"Background music {'enabled' if enabled == 'true' else 'disabled'}"})
    except Exception as e:
        return response(False, f"Toggle failed: {str(e)}", 500)

@app.route('/upload-greeting-mp3', methods=['POST'])
def upload_mp3():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file part'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No selected file'}), 400
        if not file.filename.lower().endswith('.mp3'):
            return jsonify({'success': False, 'message': 'Only MP3 files allowed'}), 400
        renamed_path = AUDIO_DIR / 'greetingaudio.mp3'
        file.save(renamed_path)
        log.info(f"Greeting MP3 uploaded: {renamed_path}")
        return jsonify({
            'success': True,
            'message': 'File uploaded and saved as greetingaudio.mp3',
            'path': str(renamed_path)
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'Upload failed: {str(e)}'}), 500

@app.route('/get-greeting-mp3/<filename>', methods=['GET'])
def get_greeting_mp3(filename):
    try:
        file_path = AUDIO_DIR / filename
        if not file_path.exists():
            return jsonify({'success': False, 'message': 'File not found'}), 404
        return send_file(file_path, mimetype='audio/mpeg')
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/next', methods=['POST'])
def next_track():
    return jsonify({"message": "Next track requested"})

@app.route('/previous', methods=['POST'])
def previous_track():
    return jsonify({"message": "Previous track requested"})

@app.route('/play-tts', methods=['POST'])
def play_tts():
    message = read_file(TTS_FILE, "Hello! Welcome.")
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
