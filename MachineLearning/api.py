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
"""

import os
import cv2
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Optional, Any
from datetime import datetime


MODEL_PATH = os.getenv("MODEL_PATH", "MachineLearning/yolov8n.pt")
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))

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

# Structure: { session_id: { target_language: str, settings: dict } }
user_sessions = {}

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
def _capture_frame():
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera index {CAMERA_INDEX}.")
    ret, frame = cap.read()
    cap.release()
    if not ret:
        raise RuntimeError("Failed to capture frame.")
    return frame


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

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'yolo_model_loaded': model is not None,
        'timestamp': datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)