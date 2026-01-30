from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import os
import tempfile
import uuid
import json
import time
from celery.result import AsyncResult
from celery_config import celery_app
import tasks  # Import tasks to register them
import logging
from state_emission import subscribe_to_job, get_latest_state

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
    return jsonify({"status": "healthy", "service": "MIRO Backend API", "streaming": True}), 200

@app.route("/analyze_full_video", methods=["POST"])
def analyze_full_video():
    """
    Main entry point. Submits video for async processing.
    Returns: Job ID + stream URL for SSE consumption.
    """
    if 'video' not in request.files:
        return jsonify({"error": "No video file provided"}), 400
        
    file = request.files['video']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    # Save file to a persistent temp location that workers can access
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
        "status": "queued",
        "stream_url": f"/stream/{task.id}"  # SSE endpoint for progressive updates
    }), 202


@app.route("/stream/<job_id>", methods=["GET"])
def stream_job(job_id):
    """
    SSE Streaming Endpoint - P0 Implementation
    
    Streams progressive state updates for a job via Server-Sent Events.
    Replaces polling with real-time push notifications.
    
    Event Format:
        event: state_update
        data: {"state": "FACE_READY", "payload": {...}, "progress_percent": 35}
    """
    def generate():
        # Send initial connection confirmation
        yield f"event: connected\ndata: {json.dumps({'job_id': job_id, 'status': 'streaming'})}\n\n"
        
        # Check for late joiner - send latest state if available
        latest = get_latest_state(job_id)
        if latest:
            yield f"event: state_update\ndata: {json.dumps(latest)}\n\n"
            if latest.get('is_terminal'):
                yield f"event: complete\ndata: {json.dumps({'job_id': job_id})}\n\n"
                return
        
        # Subscribe to Redis Pub/Sub for this job
        try:
            for state_data in subscribe_to_job(job_id):
                # Format as SSE
                yield f"event: state_update\ndata: {json.dumps(state_data)}\n\n"
                
                # If terminal state, close stream
                if state_data.get('is_terminal'):
                    yield f"event: complete\ndata: {json.dumps({'job_id': job_id, 'result_url': f'/status/{job_id}'})}\n\n"
                    break
                    
        except GeneratorExit:
            # Client disconnected
            logging.info(f"Client disconnected from stream {job_id}")
        except Exception as e:
            logging.error(f"Stream error for {job_id}: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'  # Disable nginx buffering if present
        }
    )


@app.route("/status/<job_id>", methods=["GET"])
def get_status(job_id):
    """Check job status and retrieve results if done (legacy polling fallback)"""
    task_result = AsyncResult(job_id, app=celery_app)
    
    # Also check for latest streamed state
    latest_state = get_latest_state(job_id)
    
    response = {
        "job_id": job_id,
        "status": task_result.status,
        "latest_state": latest_state.get('state') if latest_state else None,
        "progress_percent": latest_state.get('progress_percent', 0) if latest_state else 0
    }
    
    if task_result.state == 'PENDING':
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


if __name__ == "__main__":
    print("="*60)
    print("🚀 MIRO Async Backend with SSE Streaming")
    print("   • POST /analyze_full_video - Submit video")
    print("   • GET  /stream/<job_id>    - SSE progressive updates")
    print("   • GET  /status/<job_id>    - Legacy polling (fallback)")
    print("="*60)
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
