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
"""

import os
import cv2
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from ultralytics import YOLO



MODEL_PATH = os.getenv("MODEL_PATH", "MachineLearning/yolov8n.pt")
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials = True,
    allow_methods=["*"],
    allow_headers=["*"],
)


model = YOLO(MODEL_PATH)
window_name = "Camera"

cap = None

camera_should_run = True

#generate camera feed
async def generate_feed():
    global cap, camera_should_run
    while camera_should_run:
        if cap is None or not cap.isOpened():
            cap = cv2.VideoCapture(CAMERA_INDEX)
            await asyncio.sleep(0.1)
            continue

        for _ in range(2):
            cap.grab()

        success, frame = await asyncio.to_thread(cap.read)

        if not success or frame is None:
            cap.release()
            await asyncio.sleep(0.1)
            continue

        ret, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])

        if not ret:
            continue

        frame_bytes = buffer.tobytes()

        yield(b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n'
                b'ContentLength: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n'
                 + frame_bytes + b'\r\n')
            
        await asyncio.sleep(0.03)

#Camera feed
@app.get("/camFeed")
async def cam_feed():
    return StreamingResponse(generate_feed(), media_type="multipart/x-mixed-replace; boundary=frame")

#Gets a snapshot of what the AI saw
def _capture_frame():
    global cap

    if cap is None or not cap.isOpened():
        cap = cv2.VideoCapture(CAMERA_INDEX)
        raise RuntimeError(f"Cannot open camera index {CAMERA_INDEX}.")
    
    for _ in range(2):
        cap.grab()

    ret, frame = cap.read()
    if not ret:
        raise RuntimeError("Failed to capture frame.")
    
    return frame

#Gets the confidence number
@app.get("/confidence")
async def get_confidence():
    try:
        frame = _capture_frame()
        results = model(frame, verbose=False)

        best = 0.0
        for result in results:
            for box in result.boxes:
                val = float(box.conf[0])
                if val > best:
                    best = val

        return {"confidence": best}

    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

#Turns on the camera    
@app.post("/camUp")
async def camreaOn():    
    global cap, camera_should_run

    camera_should_run = True

    if cap is None or not cap.isOpened():
        cap = cv2.VideoCapture(CAMERA_INDEX)
        cap.open(CAMERA_INDEX)
        await asyncio.sleep(0.1)

    if not cap.isOpened():
        raise HTTPException(status_code=500, detail="Couldn't load camrea. Try again.")
    
    #cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
    #cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    return {"status": "Cam is on"}

#Turns off the camera
@app.post("/camDown")
async def cameraOff():
    global cap, camera_should_run

    camera_should_run = False

    if cap is not None:
        cap.release()
        cv2.destroyAllWindows()
    return {"status": "Cam is off"}

from fastapi.responses import Response

@app.get("/testSnap")
async def test_snap():
    global cap
    if cap is None or not cap.isOpened():
        return {"error": "Camera not open"}
    
    success, frame = cap.read()
    if not success:
        return {"error": "Failed to read"}
        
    _, buffer = cv2.imencode(".jpg", frame)
    return Response(content=buffer.tobytes(), media_type="image/jpeg")