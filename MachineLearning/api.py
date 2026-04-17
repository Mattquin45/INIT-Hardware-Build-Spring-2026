"""
api.py - Complete version with improved camera handling
"""

import os
import cv2
import numpy as np
import subprocess
import sys
import signal
import uuid
import atexit
import threading
import random
import time
import numpy as np
import base64
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Optional, Any
from datetime import datetime
from ultralytics import YOLO

# Add at the top with other imports
from scavenger_hunt import ScavengerHuntDetector

# Add global detector variable
scavenger_detector = None

# Try to import Google Translate (optional)
try:
    from google.cloud import translate_v2 as translate_client_lib
    TRANSLATE_AVAILABLE = True
except ImportError:
    TRANSLATE_AVAILABLE = False
    print("⚠️ Google Cloud Translate not installed. Install with: pip install google-cloud-translate")

MODEL_PATH = os.getenv("MODEL_PATH", "MachineLearning/yolov8n.pt")
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

model = YOLO(MODEL_PATH)

# Language dictionary
LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "ja": "Japanese",
    "fr": "French",
    "zh": "Chinese",
    "ko": "Korean",
    "it": "Italian",
    "de": "German",
    "el": "Greek",
    "ru": "Russian",
    "ar": "Arabic",
    "ur": "Urdu",
    "hi": "Hindi",
    "ht": "Haitian Creole",
    "pt": "Portuguese",
    "ro": "Romanian",
    "fa": "Persian",
}

# YOLO's 80 built-in class names (yolov8n)
YOLO_CLASSES = [
    "table", "chair", "whiteboard", "bookshelf", "clock", 
    "wall-magazine", "trash-can", "eraser", "sharpener", "pen", 
    "book", "ruler", "scissor", "fan", "laptop", 
    "remote-control", "bag", "pants", "shoes", "hat"
]

# Initialize Google Translate client if available
if TRANSLATE_AVAILABLE:
    try:
        translate_client = translate_client_lib.Client()
        print("✅ Google Translate client initialized")
    except Exception as e:
        print(f"⚠️ Google Translate initialization failed: {e}")
        translate_client = None
else:
    translate_client = None

# Structure: { session_id: { target_language: str, settings: dict } }
user_sessions = {}
webcam_processes = {}

# Global game state (one game at a time)
game_state = {
    "active": False,
    "targets": [],        # [{"en": "cup", "translated": "taza", "found": False}]
    "start_time": None,
    "duration": 60,       # seconds
    "language": "en",
}

# Camera management
camera = None
camera_lock = threading.Lock()
camera_last_used = None
camera_timeout = 5  # Release camera after 5 seconds of inactivity

# Pydantic models for request/response
class LanguageUpdateRequest(BaseModel):
    targetLanguage: str
    settings: Optional[Dict[str, bool]] = None

class SettingsUpdateRequest(BaseModel):
    settings: Dict[str, bool]

class LanguageResponse(BaseModel):
    success: bool
    language: str
    languageName: str
    settings: Optional[Dict[str, bool]] = None
    message: str
    timestamp: str

class WebcamStartRequest(BaseModel):
    session_id: Optional[str] = None
    model_path: Optional[str] = None
    conf_threshold: Optional[float] = 0.35

class ScavengerStartRequest(BaseModel):
    num_items: Optional[int] = 5
    duration: Optional[int] = 60  # seconds

def get_session_id(request: Request) -> str:
    """Get or create session ID from cookies or headers"""
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = request.headers.get("X-Session-ID")
    if not session_id:
        session_id = str(uuid.uuid4())
    return session_id

def get_user_session(session_id: str) -> dict:
    """Get or create user session"""
    if session_id not in user_sessions:
        user_sessions[session_id] = {
            'target_language': 'en',
            'settings': {
                'online': False,
                'en': False,
                'es': False
            }
        }
    return user_sessions[session_id]

def translate_word(word: str, lang: str) -> str:
    """Translate a single word, return original if English or error."""
    if lang == "en":
        return word
    if not translate_client:
        return word
    try:
        result = translate_client.translate(word, target_language=lang)
        return result["translatedText"]
    except Exception as e:
        print(f"Translation error for '{word}': {e}")
        return word

def get_camera():
    """Get or create a persistent camera instance"""
    global camera, camera_last_used
    
    with camera_lock:
        # Check if we need to release old camera (timeout)
        if camera_last_used and (time.time() - camera_last_used) > camera_timeout:
            release_camera()
        
        # Create new camera if needed
        if camera is None:
            try:
                # Try different camera indices if default fails
                for idx in [CAMERA_INDEX, 0, 1, 2]:
                    print(f"Attempting to open camera index {idx}...")
                    cap = cv2.VideoCapture(idx)
                    if cap.isOpened():
                        camera = cap
                        print(f"✅ Successfully opened camera index {idx}")
                        break
                    else:
                        cap.release()
                
                if camera is None:
                    raise RuntimeError(f"Cannot open any camera. Tried indices: {CAMERA_INDEX}, 0, 1, 2")
                
                # Set camera properties for better performance
                camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer to get latest frame
                
            except Exception as e:
                print(f"Error opening camera: {e}")
                raise RuntimeError(f"Cannot open camera: {e}")
        
        camera_last_used = time.time()
        return camera

def release_camera():
    """Release the camera when done"""
    global camera, camera_last_used
    with camera_lock:
        if camera is not None:
            camera.release()
            camera = None
            camera_last_used = None
            print("📷 Camera released")

def capture_frame_with_retry(max_retries=3):
    """Capture a frame with retry logic"""
    for attempt in range(max_retries):
        try:
            cap = get_camera()
            ret, frame = cap.read()
            if ret and frame is not None:
                return frame
            else:
                print(f"Failed to capture frame, attempt {attempt + 1}/{max_retries}")
                # Release and recreate camera on failure
                release_camera()
                time.sleep(0.5)
        except Exception as e:
            print(f"Error capturing frame (attempt {attempt + 1}): {e}")
            release_camera()
            time.sleep(0.5)
    
    raise RuntimeError("Failed to capture frame after multiple attempts")

# Register cleanup on exit
atexit.register(release_camera)

@app.get("/confidence")
def get_confidence():
    try:
        frame = capture_frame_with_retry()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    results = model(frame, verbose=False)
    best = 0.0
    for result in results:
        for box in result.boxes:
            val = float(box.conf[0])
            if val > best:
                best = val

    return {"confidence": best}

@app.post("/api/webcam/start")
async def start_webcam_tester(request: WebcamStartRequest, fastapi_request: Request):
    """Start the YOLO webcam tester with current language settings"""
    try:
        # Get session ID and user preferences
        session_id = get_session_id(fastapi_request)
        session = get_user_session(session_id)
        
        # Check if webcam is already running for this session
        if session_id in webcam_processes and webcam_processes[session_id].poll() is None:
            return JSONResponse(
                status_code=400,
                content={
                    'success': False,
                    'message': 'Webcam tester is already running',
                    'session_id': session_id
                }
            )
        
        # Get current language from session
        target_language = session['target_language']
        language_name = LANGUAGES.get(target_language, "English")
        
        # Get the directory where api.py is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(current_dir, "webcam_tester_google.py")
        
        print(f"Looking for script at: {script_path}")
        
        if not os.path.exists(script_path):
            raise HTTPException(
                status_code=404, 
                detail=f"Webcam tester script not found at {script_path}"
            )
        
        # Model path - use best.onnx if it exists
        model_path = request.model_path
        if not model_path:
            best_onnx = os.path.join(current_dir, "best.onnx")
            if os.path.exists(best_onnx):
                model_path = best_onnx
            else:
                model_path = "yolov8n.pt"
        
        conf_threshold = str(request.conf_threshold)
        
        # Release our camera before starting subprocess
        release_camera()
        
        # Run the webcam tester as a subprocess
        cmd = [
            sys.executable,
            script_path,
            model_path,
            "--conf", conf_threshold,
            "--lang", target_language
        ]
        
        print(f"🚀 Starting webcam tester: {' '.join(cmd)}")
        
        # Start the process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        webcam_processes[session_id] = process
        
        import asyncio
        await asyncio.sleep(1)
        
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            error_msg = f"Process died immediately. stderr: {stderr}, stdout: {stdout}"
            print(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
        
        return {
            'success': True,
            'message': f'Webcam tester started with language: {language_name}',
            'session_id': session_id,
            'target_language': target_language,
            'language_name': language_name,
            'model_path': model_path,
            'conf_threshold': request.conf_threshold,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error starting webcam: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/webcam/stop")
async def stop_webcam_tester(fastapi_request: Request):
    """Stop the running webcam tester"""
    session_id = get_session_id(fastapi_request)
    
    if session_id not in webcam_processes:
        return JSONResponse(
            status_code=404,
            content={
                'success': False,
                'message': 'No webcam tester running for this session'
            }
        )
    
    process = webcam_processes[session_id]
    
    if process.poll() is None:
        try:
            if sys.platform == 'win32':
                process.terminate()
            else:
                process.send_signal(signal.SIGINT)
            
            process.wait(timeout=5)
            
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        
        del webcam_processes[session_id]
        
        return {
            'success': True,
            'message': 'Webcam tester stopped successfully',
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        }
    else:
        del webcam_processes[session_id]
        return {
            'success': True,
            'message': 'Webcam tester was not running',
            'session_id': session_id
        }

@app.get("/api/webcam/status")
async def get_webcam_status(fastapi_request: Request):
    """Check if webcam tester is running"""
    session_id = get_session_id(fastapi_request)
    
    is_running = False
    if session_id in webcam_processes:
        process = webcam_processes[session_id]
        is_running = process.poll() is None
    
    return {
        'running': is_running,
        'session_id': session_id,
        'timestamp': datetime.now().isoformat()
    }

# ============ Language Management Endpoints ============
@app.get("/api/language")
async def get_language(request: Request):
    """Get current language settings"""
    session_id = get_session_id(request)
    session = get_user_session(session_id)
    
    response_data = {
        'success': True,
        'currentLanguage': session['target_language'],
        'languageName': LANGUAGES.get(session['target_language']),
        'availableLanguages': LANGUAGES,
        'settings': session['settings'],
        'timestamp': datetime.now().isoformat()
    }
    
    response = JSONResponse(content=response_data)
    response.set_cookie(key="session_id", value=session_id, httponly=False, max_age=3600*24*30)
    
    return response

@app.post("/api/language")
async def update_language(request: LanguageUpdateRequest, fastapi_request: Request):
    """Update target language"""
    session_id = get_session_id(fastapi_request)
    session = get_user_session(session_id)
    
    if request.targetLanguage not in LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid language: {request.targetLanguage}"
        )
    
    session['target_language'] = request.targetLanguage
    
    if request.settings:
        session['settings'].update(request.settings)
    
    response_data = {
        'success': True,
        'language': request.targetLanguage,
        'languageName': LANGUAGES[request.targetLanguage],
        'settings': session['settings'],
        'message': f"Language changed to {LANGUAGES[request.targetLanguage]}",
        'timestamp': datetime.now().isoformat()
    }
    
    response = JSONResponse(content=response_data)
    response.set_cookie(key="session_id", value=session_id, httponly=False, max_age=3600*24*30)
    
    return response

@app.get("/api/languages")
async def get_languages():
    """Get all available languages"""
    return LANGUAGES

@app.post("/api/settings")
async def update_settings(request: SettingsUpdateRequest, fastapi_request: Request):
    """Update all settings"""
    session_id = get_session_id(fastapi_request)
    session = get_user_session(session_id)
    
    session['settings'] = request.settings
    
    response_data = {
        'success': True,
        'settings': request.settings,
        'message': 'Settings updated successfully',
        'timestamp': datetime.now().isoformat()
    }
    
    response = JSONResponse(content=response_data)
    response.set_cookie(key="session_id", value=session_id, httponly=False, max_age=3600*24*30)
    
    return response

# ============ Scavenger Hunt Endpoints ============

@app.post("/api/scavenger/start")
async def start_scavenger(request: ScavengerStartRequest, fastapi_request: Request):
    """Start a new scavenger hunt game."""
    global scavenger_detector
    
    session_id = get_session_id(fastapi_request)
    session = get_user_session(session_id)
    language = session["target_language"]

    # Stop any existing detector
    if scavenger_detector:
        scavenger_detector.stop_detection()
        scavenger_detector = None
    
    # Pick random objects
    num_items = min(request.num_items, len(YOLO_CLASSES))
    chosen = random.sample(YOLO_CLASSES, num_items)

    # Translate them
    targets = []
    for word in chosen:
        translated = translate_word(word, language)
        targets.append({"en": word, "translated": translated, "found": False})

    # Initialize game state
    game_state["active"] = True
    game_state["targets"] = targets
    game_state["start_time"] = time.time()
    game_state["duration"] = request.duration
    game_state["language"] = language
    
    # Start the detector in background with display window
    try:
        model_path = os.path.join(os.path.dirname(__file__), "best.onnx")
        if not os.path.exists(model_path):
            model_path = "yolov8n.pt"
        
        from scavenger_hunt import ScavengerHuntDetector
        scavenger_detector = ScavengerHuntDetector(
            model_path=model_path,
            target_language=language,
            conf=0.35,
            camera_index=CAMERA_INDEX
        )
        
        # Define callback to update game state when objects are found
        def detection_callback(detections):
            if not game_state["active"]:
                return
            
            # Check each detection against targets
            updated = False
            for detection in detections:
                for target in game_state["targets"]:
                    if not target["found"] and target["en"].lower() == detection["label_en"].lower():
                        target["found"] = True
                        updated = True
                        print(f"🎉 Found {target['en']} ({target['translated']})!")
                        
                        # Check if all found
                        if all(t["found"] for t in game_state["targets"]):
                            print("🎉🎉🎉 ALL ITEMS FOUND! 🎉🎉🎉")
                            game_state["active"] = False
                            # Stop detector after a delay
                            threading.Timer(2.0, lambda: scavenger_detector.stop_detection() if scavenger_detector else None).start()
            
            # If game ended, stop detector
            if not game_state["active"] and scavenger_detector:
                scavenger_detector.stop_detection()
        
        # Start detection with targets
        scavenger_detector.start_detection(targets, detection_callback)
        
    except Exception as e:
        print(f"Error starting detector: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

    return {
        "success": True,
        "targets": targets,
        "duration": request.duration,
        "language": language,
    }


@app.get("/api/scavenger/status")
async def scavenger_status():
    """Poll this every second from React to get current game state."""
    if not game_state["active"]:
        return {"active": False, "time_left": 0, "targets": game_state["targets"], "all_found": False}

    elapsed = time.time() - game_state["start_time"]
    time_left = max(0, game_state["duration"] - elapsed)
    
    all_found = all(t["found"] for t in game_state["targets"])
    
    if time_left == 0 or all_found:
        game_state["active"] = False

    return {
        "active": game_state["active"],
        "targets": game_state["targets"],
        "time_left": int(time_left),
        "all_found": all_found,
    }

# Update stop_scavenger endpoint
@app.post("/api/scavenger/stop")
async def stop_scavenger():
    """Stop the current game."""
    global scavenger_detector
    
    game_state["active"] = False
    
    if scavenger_detector:
        scavenger_detector.stop_detection()
        scavenger_detector = None
    
    release_camera()
    return {"success": True} 


@app.post("/api/detect")
async def detect_objects(request: Request):
    """Detect objects in uploaded image"""
    try:
        # Read uploaded image
        form = await request.form()
        image_file = form.get("image")
        
        if not image_file:
            return {"objects": []}
        
        # Read image file
        contents = await image_file.read()
        
        # Convert to numpy array
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return {"objects": []}
        
        # Run inference
        results = model(img, conf=0.35, verbose=False)
        
        # Parse detections
        detections = []
        for result in results:
            if result.boxes is not None:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    label = result.names[cls]
                    
                    detections.append({
                        "label": label,
                        "confidence": conf,
                        "bbox": [int(x1), int(y1), int(x2 - x1), int(y2 - y1)]
                    })
        
        return {"objects": detections}
        
    except Exception as e:
        print(f"Detection error: {e}")
        import traceback
        traceback.print_exc()
        return {"objects": []}

@app.post("/api/scavenger/update")
async def update_scavenger(request: Request):
    """Update targets from frontend"""
    try:
        data = await request.json()
        if "targets" in data:
            game_state["targets"] = data["targets"]
        return {"success": True}
    except Exception as e:
        print(f"Update error: {e}")
        return {"success": False}
    

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'yolo_model_loaded': model is not None,
        'translate_available': translate_client is not None,
        'camera_available': camera is not None and camera.isOpened() if camera else False,
        'timestamp': datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)