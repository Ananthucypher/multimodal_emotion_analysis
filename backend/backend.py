from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import tempfile
import uuid
from celery.result import AsyncResult
from celery_config import celery_app
import tasks  # Import tasks to register them
import logging

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__)

# Config
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 500 * 1024 * 1024)) # 500MB
allowed_origins = os.getenv('ALLOWED_ORIGINS', '*').split(',')
CORS(app, origins=allowed_origins if allowed_origins != ['*'] else '*')

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'webm', 'mkv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- ROUTES ---

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "MIRO Backend API"}), 200

@app.route("/analyze_full_video", methods=["POST"])
def analyze_full_video():
    """
    Main entry point. Submits video for async processing.
    Returns: Job ID.
    Currently maintains backward compatibility by returning 'job_id' 
    Users/Frontend need to poll /status/<job_id>
    """
    if 'video' not in request.files:
        return jsonify({"error": "No video file provided"}), 400
        
    file = request.files['video']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    # Save file to a persistent temp location that workers can access
    # Note: In production with distributed workers, this should be S3/Shared Volume.
    # For local Celery, /tmp or local path works.
    upload_dir = os.path.join(tempfile.gettempdir(), "miro_uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    filename = f"{uuid.uuid4()}_{file.filename}"
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)
    
    try:
        # Submit Job
        task = tasks.process_video_job.delay(filepath)
    except Exception as e:
        logging.error(f"Failed to submit job to Celery: {e}")
        return jsonify({
            "error": "Job submission failed", 
            "message": "Could not connect to background worker. Is Redis running?",
            "details": str(e)
        }), 500
    
    return jsonify({
        "message": "Video submitted for processing",
        "job_id": task.id,
        "status": "queued"
    }), 202

@app.route("/status/<job_id>", methods=["GET"])
def get_status(job_id):
    """Check job status and retrieve results if done"""
    task_result = AsyncResult(job_id, app=celery_app)
    
    response = {
        "job_id": job_id,
        "status": task_result.status,
    }
    
    if task_result.state == 'PENDING':
        # Job has not started yet
        response.update({"progress": 0, "message": "Job is queued..."})
        
    elif task_result.state == 'PROGRESS':
        meta = task_result.info
        response.update({
            "progress": meta.get('current', 0),
            "total": meta.get('total', 100),
            "message": meta.get('status', 'Processing...')
        })
        
    elif task_result.state == 'SUCCESS':
        response.update({
            "progress": 100,
            "result": task_result.result,
            "status": "completed"
        })
        
    elif task_result.state == 'FAILURE':
        response.update({
            "error": str(task_result.info), 
            "status": "failed"
        })
        
    return jsonify(response)

# Legacy/Sync route fallback if frontend is unaware of async (Optional)
# For this upgrade, we assume we will update frontend or use a proxy.
# But existing frontend calls /analyze_full_video expecting immediate JSON.
# WE BREAK COMPATIBILITY HERE, AS PLANNED. Frontend updates needed next.

if __name__ == "__main__":
    print("="*60)
    print("🚀 MIRO Async Backend Starting...")
    print("Use 'celery -A celery_config.celery_app worker --loglevel=info' to start worker")
    print("="*60)
    app.run(host="0.0.0.0", port=5000, debug=True)
