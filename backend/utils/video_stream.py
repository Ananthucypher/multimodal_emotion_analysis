import os
import subprocess
import glob
import logging

logger = logging.getLogger(__name__)

def get_video_duration(video_path):
    """Get video duration in seconds using ffprobe"""
    try:
        cmd = [
            'ffprobe', 
            '-v', 'error', 
            '-show_entries', 'format=duration', 
            '-of', 'default=noprint_wrappers=1:nokey=1', 
            video_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return float(result.stdout.strip())
    except Exception as e:
        logger.error(f"Error getting duration: {e}")
        return 0.0

def stream_segments(video_path, segment_duration=5, output_dir=None):
    """
    Split video into segments using FFmpeg without loading full video into memory.
    Returns: Generator yielding paths to segment files.
    """
    if output_dir is None:
        output_dir = os.path.dirname(video_path)
    
    # Base pattern for segment filenames
    segment_pattern = os.path.join(output_dir, "segment_%03d.mp4")
    
    # Ensure no stale segments exist
    for f in glob.glob(os.path.join(output_dir, "segment_*.mp4")):
        try:
            os.remove(f)
        except OSError:
            pass

    try:
        # FFmpeg command to segment video
        # -c copy is fast (stream copy) but requires keyframes at cut points.
        # For precise cutting, we might need re-encoding, but let's try copy first for speed.
        # If copy fails or is imprecise, we can remove '-c copy'.
        cmd = [
            'ffmpeg', '-i', video_path,
            '-f', 'segment', 
            '-segment_time', str(segment_duration),
            '-c', 'copy', 
            '-reset_timestamps', '1',
            '-map', '0',
            segment_pattern
        ]
        
        logger.info(f"Starting segmentation: {' '.join(cmd)}")
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        
        # Yield generated segments in order
        segments = sorted(glob.glob(os.path.join(output_dir, "segment_*.mp4")))
        for segment in segments:
            yield segment
            
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg segmentation failed: {e.stderr.decode()}")
        raise
    except Exception as e:
        logger.error(f"Segmentation error: {e}")
        raise

def cleanup_segments(directory, pattern="segment_*.mp4"):
    """Clean up segment files"""
    for f in glob.glob(os.path.join(directory, pattern)):
        try:
            os.remove(f)
        except OSError:
            pass
