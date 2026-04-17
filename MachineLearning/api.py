
"""
api.py

FastAPI server that exposes YOLO model confidence to the React frontend.

Usage:
    uvicorn MachineLearning.api:app --reload

Environment variables:
    MODEL_PATH   Path to the .pt model file (default: MachineLearning/yolov8n.pt)
    CAMERA_INDEX Webcam device index (default: 0)

Endpoints:
    GET /confidence  Returns the highest confidence score from a single inference frame.
                     {"confidence": 0.87}  — or {"confidence": 0.0} if no detections.
    GET /api/language         Returns current language settings
    POST /api/language        Updates target language
    GET /api/languages        Returns all available languages
    POST /api/settings        Updates user settings
    POST /api/webcam/start    Starts the webcam tester with current language settings
    POST /api/webcam/stop     Stops the webcam tester (if running)
    POST /api/scavenger/start Starts a new scavenger hunt game
    GET /api/scavenger/status Gets current scavenger hunt status
    POST /api/scavenger/stop  Stops the current scavenger hunt game
"""


import os
import cv2
import subprocess
import sys
import signal
import uuid
import atexit
import threading
import random
import time
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Optional, Any
from datetime import datetime
from ultralytics import YOLO

# Try to import Google Translate (optional)
try:
    from google.cloud import translate_v2 as translate_client_lib
    TRANSLATE_AVAILABLE = True
except ImportError:
    TRANSLATE_AVAILABLE = False
    print("⚠️ Google Cloud Translate not installed. Install with: pip install google-cloud-translate")

MODEL_PATH = os.getenv("MODEL_PATH", "MachineLearning/yolov8n.pt")
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))

# Add at the top with other global variables
camera = None
camera_lock = threading.Lock()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"], # Your React dev servers
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
    "person","bicycle","car","motorcycle","airplane","bus","train","truck","boat",
    "traffic light","fire hydrant","stop sign","parking meter","bench","bird","cat",
    "dog","horse","sheep","cow","elephant","bear","zebra","giraffe","backpack",
    "umbrella","handbag","tie","suitcase","frisbee","skis","snowboard","sports ball",
    "kite","baseball bat","baseball glove","skateboard","surfboard","tennis racket",
    "bottle","wine glass","cup","fork","knife","spoon","bowl","banana","apple",
    "sandwich","orange","broccoli","carrot","hot dog","pizza","donut","cake","chair",
    "couch","potted plant","bed","dining table","toilet","tv","laptop","mouse",
    "remote","keyboard","cell phone","microwave","oven","toaster","sink","refrigerator",
    "book","clock","vase","scissors","teddy bear","hair drier","toothbrush"
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
        # Generate a simple session ID (you can use uuid in production)
        import uuid
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

def _capture_frame():
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera index {CAMERA_INDEX}.")
    ret, frame = cap.read()
    cap.release()
    if not ret:
        raise RuntimeError("Failed to capture frame.")
    return frame

def get_camera():
    """Get or create a persistent camera instance"""
    global camera
    with camera_lock:
        if camera is None or not camera.isOpened():
            camera = cv2.VideoCapture(CAMERA_INDEX)
            if not camera.isOpened():
                raise RuntimeError(f"Cannot open camera index {CAMERA_INDEX}.")
        return camera

def release_camera():
    """Release the camera when done"""
    global camera
    with camera_lock:
        if camera is not None:
            camera.release()
            camera = None

# Register cleanup on exit
atexit.register(release_camera)

# Then modify _capture_frame to use the persistent camera:
def _capture_frame():
    """Capture a frame using persistent camera connection"""
    try:
        cap = get_camera()
        ret, frame = cap.read()
        if not ret:
            raise RuntimeError("Failed to capture frame.")
        return frame
    except Exception as e:
        # If there's an error, try to reinitialize
        release_camera()
        raise e


@app.get("/confidence")
def get_confidence():
    try:
        frame = _capture_frame()
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
        
        print(f"Looking for script at: {script_path}")  # Debug print
        
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
        
        print(f"🚀 Starting webcam tester:")
        print(f"   Script: {script_path}")
        print(f"   Model: {model_path}")
        print(f"   Language: {target_language}")
        print(f"   Python: {sys.executable}")
        
        # Run the webcam tester as a subprocess
        cmd = [
            sys.executable,
            script_path,
            model_path,
            "--conf", conf_threshold,
            "--lang", target_language
        ]
        
        print(f"   Command: {' '.join(cmd)}")
        
        # Start the process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Store the process
        webcam_processes[session_id] = process
        
        # Give it a moment to start
        import asyncio
        await asyncio.sleep(1)
        
        # Check if process is still running
        if process.poll() is not None:
            # Process died, read error
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
    
    if process.poll() is None:  # Process is still running
        try:
            # Try to terminate gracefully
            if sys.platform == 'win32':
                process.terminate()
            else:
                process.send_signal(signal.SIGINT)  # Simulate Ctrl+C
            
            # Wait for process to terminate
            process.wait(timeout=5)
            
        except subprocess.TimeoutExpired:
            # Force kill if not responding
            process.kill()
            process.wait()
        
        # Remove from tracking
        del webcam_processes[session_id]
        
        return {
            'success': True,
            'message': 'Webcam tester stopped successfully',
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        }
    else:
        # Process already ended
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
    
    # Create response with session cookie
    response = JSONResponse(content=response_data)
    response.set_cookie(key="session_id", value=session_id, httponly=False, max_age=3600*24*30)
    
    return response

@app.post("/api/language")
async def update_language(request: LanguageUpdateRequest, fastapi_request: Request):
    """Update target language"""
    session_id = get_session_id(fastapi_request)
    session = get_user_session(session_id)
    
    # Validate language
    if request.targetLanguage not in LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid language: {request.targetLanguage}"
        )
    
    # Update language
    session['target_language'] = request.targetLanguage
    
    # Update settings if provided
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
    session_id = get_session_id(fastapi_request)
    session = get_user_session(session_id)
    language = session["target_language"]

    # Pick random objects
    num_items = min(request.num_items, len(YOLO_CLASSES))
    chosen = random.sample(YOLO_CLASSES, num_items)

    # Translate them
    targets = []
    for word in chosen:
        translated = translate_word(word, language)
        targets.append({"en": word, "translated": translated, "found": False})

    game_state["active"] = True
    game_state["targets"] = targets
    game_state["start_time"] = time.time()
    game_state["duration"] = request.duration
    game_state["language"] = language

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
        return {"active": False}

    elapsed = time.time() - game_state["start_time"]
    time_left = max(0, game_state["duration"] - elapsed)

    # Run a quick inference frame to check for found objects
    try:
        frame = _capture_frame()
        results = model(frame, conf=0.35, verbose=False)
        detected = set()
        for result in results:
            for box in result.boxes:
                label = result.names[int(box.cls[0])]
                detected.add(label)

        # Mark targets as found
        for target in game_state["targets"]:
            if target["en"] in detected:
                target["found"] = True
    except Exception as e:
        print(f"Inference error in scavenger status: {e}")

    all_found = all(t["found"] for t in game_state["targets"])
    if time_left == 0 or all_found:
        game_state["active"] = False

    return {
        "active": game_state["active"],
        "targets": game_state["targets"],
        "time_left": int(time_left),
        "all_found": all_found,
    }

@app.post("/api/scavenger/stop")
async def stop_scavenger():
    """Stop the current game."""
    game_state["active"] = False
    return {"success": True}

# Add an endpoint to release camera when game ends
@app.post("/api/scavenger/stop")
async def stop_scavenger():
    """Stop the current game."""
    global game_state
    game_state["active"] = False
    release_camera()  # Release camera when game stops
    return {"success": True}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'yolo_model_loaded': model is not None,
        'translate_available': translate_client is not None,
        'timestamp': datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)