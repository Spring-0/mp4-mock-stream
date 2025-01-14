from flask import Flask, send_from_directory, request
import os
import subprocess
from flask_cors import CORS
import threading
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

app = Flask(__name__)

CORS(app, resources={
    r"/*": {
        "origins": ["https://mp4-hls-mocker.netlify.app"],
        "methods": ["POST", "GET", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

UPLOAD_FOLDER = "uploads"
HLS_FOLDER = "hls_output"
ALLOWED_EXTENSIONS = {"mp4"}
FILE_EXPIRY_MINUTES = 60

file_timestamps = {}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(HLS_FOLDER, exist_ok=True)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_to_hls(input_path, output_path):
    try:
        command = [
            "ffmpeg",
            "-i", input_path,
            "-profile:v", "baseline",
            "-level", "3.0",
            "-start_number", "0",
            "-hls_time", "10",
            "-hls_list_size", "0",
            "-f", "hls",
            output_path
        ]
        
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            print(f"FFmpeg error: {stderr.decode()}")
            return False
        return True
    except Exception as e:
        print(f"Conversion error: {str(e)}")
        return False

def cleanup_expired_files():
    current_time = datetime.now()
    expired_files = []

    for filename, timestamp in file_timestamps.items():
        if current_time - timestamp > timedelta(minutes=FILE_EXPIRY_MINUTES):
            print("Found expired file: ", filename)
            expired_files.append(filename)

    for filename in expired_files:
        try:
            mp4_path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.exists(mp4_path):
                os.remove(mp4_path)

            output_filename = os.path.splitext(filename)[0]
            hls_directory = os.path.join(HLS_FOLDER, output_filename)
            if os.path.exists(hls_directory):
                for file in os.listdir(hls_directory):
                    os.remove(os.path.join(hls_directory, file))
                os.rmdir(hls_directory)

            del file_timestamps[filename]
            print(f"Cleaned up expired files for {filename}")
        except Exception as e:
            print(f"Error cleaning up {filename}: {str(e)}")


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return {"error": "No file found"}, 400
    
    file = request.files["file"]
    if file.filename == "":
        return {"error": "No file found"}, 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)
        
        file_timestamps[filename] = datetime.now()
        
        output_filename = os.path.splitext(filename)[0]
        output_path = os.path.join(HLS_FOLDER, f"{output_filename}/playlist.m3u8")
        os.makedirs(os.path.join(HLS_FOLDER, output_filename), exist_ok=True)
        
        thread = threading.Thread(target=convert_to_hls, args=(input_path, output_path))
        thread.start()
        
        expiry_time = datetime.now() + timedelta(minutes=FILE_EXPIRY_MINUTES)
        return {
            "message": "Conversion Success",
            "stream_url": f"https://mp4-mock-stream.onrender.com/stream/{output_filename}/playlist.m3u8",
            "expires_at": expiry_time.isoformat()
        }
    
    return {"error": "File type not allowed"}, 400


@app.route("/stream/<path:filename>")
def serve_hls(filename):
    base_filename = filename.split('/')[0] + '.mp4'
    if base_filename in file_timestamps:
        if datetime.now() - file_timestamps[base_filename] > timedelta(minutes=FILE_EXPIRY_MINUTES):
            return {"error": "Stream has expired"}, 410

    return send_from_directory(HLS_FOLDER, filename)


def init_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        cleanup_expired_files,
        trigger=IntervalTrigger(minutes=10),
        id='cleanup_job',
        name='Remove expired files',
        replace_existing=True
    )
    scheduler.start()

if __name__ == "__main__":
    from waitress import serve
    init_scheduler()
    # app.run(host="0.0.0.0", port=5000, debug=True)
    serve(app, host="0.0.0.0", port=8080)