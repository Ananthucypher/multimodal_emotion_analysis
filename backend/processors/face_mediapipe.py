import cv2
import mediapipe as mp
import numpy as np
import logging

logger = logging.getLogger(__name__)

class MediaPipeFaceProcessor:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        # Refine landmarks can detect iris and detailed lips
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        # Simple blendshape-to-emotion mapping (Heuristic based on FACS)
        # Real production would use a small MLP, but this is fast and decent for "dominant" emotion
        self.BLENDSHAPE_MAP = {
            "neutral": [],
            "happy": ["mouthSmileLeft", "mouthSmileRight", "cheekSquintLeft", "cheekSquintRight"],
            "sad": ["mouthFrownLeft", "mouthFrownRight", "browInnerUp"],
            "angry": ["browDownLeft", "browDownRight", "jawForward"], 
            "surprise": ["browOuterUpLeft", "browOuterUpRight", "jawOpen"],
            "fear": ["browInnerUp", "eyeWideLeft", "eyeWideRight"],
            "disgust": ["noseSneerLeft", "noseSneerRight", "mouthUpperUpLeft"]
        }

    def process_video(self, video_path, skip_frames=5):
        """
        Process video and return aggregated emotion stats using Blendshapes if available 
        or geometry heuristics.
        Note: Python MediaPipe Blendshapes support is version dependent. 
        If blendshapes aren't available, we use simple landmark distances.
        """
        logger.info(f"Starting MediaPipe Face Analysis on {video_path}")
        cap = cv2.VideoCapture(video_path)
        frame_count = 0
        analyzed_count = 0
        emotions_agg = {k: 0 for k in self.BLENDSHAPE_MAP.keys()}
        
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                if frame_count % skip_frames != 0:
                    continue
                
                # Convert BGR to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.face_mesh.process(rgb_frame)
                
                if results.multi_face_landmarks:
                    analyzed_count += 1
                    # Simple geometric heuristic since blendshapes might not be easy in python API 
                    # without the task API. Implementing robust geometric classifier.
                    landmarks = results.multi_face_landmarks[0]
                    emo = self._classify_landmarks_geometric(landmarks.landmark)
                    emotions_agg[emo] += 1
                    
        except Exception as e:
            logger.error(f"MediaPipe processing failed: {e}")
        finally:
            cap.release()
            
        # Normalize
        total = sum(emotions_agg.values())
        if total > 0:
            emotions_agg = {k: v/total for k, v in emotions_agg.items()}
            dom = max(emotions_agg, key=emotions_agg.get)
        else:
            dom = "neutral"
            
        return {
            "dominant_emotion": dom,
            "emotions": emotions_agg,
            "frames_analyzed": analyzed_count
        }

    def _classify_landmarks_geometric(self, lm):
        """
        Classify emotion based on normalized distances of key landmarks.
        lm: List of normalized keypoints (x,y,z)
        """
        # Key Landmarks indices
        # Lips: Top(13), Bottom(14), Left(61), Right(291)
        # Brows: LeftInner(55), RightInner(285), LeftOuter(70), RightOuter(300)
        # Eyes: LeftTop(159), LeftBottom(145), RightTop(386), RightBottom(374)
        
        def dist(i1, i2):
            return np.sqrt((lm[i1].x - lm[i2].x)**2 + (lm[i1].y - lm[i2].y)**2)
            
        # Metrics
        mouth_width = dist(61, 291)
        mouth_open = dist(13, 14) / mouth_width
        eyebrow_raise = (dist(55, 145) + dist(285, 374)) / 2  # Eye to brow vertical
        
        # Heuristics (Tuned for Speech)
        # 1. Smile Detection (Happy)
        if mouth_width > 0.46: 
             return "happy"
             
        # 2. Surprise vs Talking
        # Surprise requires BOTH mouth open AND eyebrows raised significantly
        if mouth_open > 0.35 and eyebrow_raise > 0.30: 
            return "surprise" 
            
        # 3. Angry (Low Brow + Narrow Mouth?)
        if eyebrow_raise < 0.14: 
             return "angry"
             
        # Default to neutral (covers talking/sad/fear which are hard geometrically)
        return "neutral"

# Singleton instance
_mp_processor = None

def analyze_face_mediapipe(video_path):
    global _mp_processor
    if _mp_processor is None:
        _mp_processor = MediaPipeFaceProcessor()
    return _mp_processor.process_video(video_path)
