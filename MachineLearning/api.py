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
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO

MODEL_PATH = os.getenv("MODEL_PATH", "MachineLearning/yolov8n.pt")
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

model = YOLO(MODEL_PATH)


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
