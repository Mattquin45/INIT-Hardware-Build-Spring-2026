# scavenger_hunt.py
import cv2
import sys
import time
import threading
import json
import os
from ultralytics import YOLO
from google.cloud import translate_v2 as translate
from google.oauth2 import service_account

class ScavengerHuntDetector:
    """
    Runs YOLO detection in the background for the scavenger hunt game
    """
    
    def __init__(self, model_path, target_language="en", conf=0.35, camera_index=0):
        # Load model
        self.model = YOLO(model_path)
        self.target_language = target_language
        self.conf = conf
        self.camera_index = camera_index
        self.running = False
        self.current_detections = []
        self.found_items = set()
        self.window_name = "Scavenger Hunt - Point camera at objects"
        
        # Initialize Google Translate
        self.translate_client = None
        self.init_translate()
        
        # Open camera
        self.cap = None
        self.label_cache = {}  # Cache for translations
        
    def init_translate(self):
        """Initialize Google Translate client"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            key_path = os.path.join(script_dir, "keys", "civil-oarlock-492721-d0-3c7e6b42df7a.json")
            
            if os.path.exists(key_path):
                credentials = service_account.Credentials.from_service_account_file(key_path)
                self.translate_client = translate.Client(credentials=credentials)
                print("✅ Google Translate initialized")
            else:
                print("⚠️ Translation key not found, using English only")
        except Exception as e:
            print(f"⚠️ Translation error: {e}")
    
    def translate_label(self, label):
        """Translate label to target language with caching"""
        if self.target_language == "en" or not self.translate_client:
            return label
        
        if label in self.label_cache:
            return self.label_cache[label]
            
        try:
            result = self.translate_client.translate(label, target_language=self.target_language)
            translated = result["translatedText"]
            self.label_cache[label] = translated
            return translated
        except:
            return label
    
    def draw_detections(self, frame, detections, targets):
        """Draw bounding boxes and info on frame"""
        overlay = frame.copy()
        
        # Draw detections
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            label = det["label"]
            conf = det["confidence"]
            
            # Check if this is a target item
            is_target = False
            for target in targets:
                if target["en"].lower() == det["label_en"].lower() and not target["found"]:
                    is_target = True
                    break
            
            # Choose color: Green for targets, Red for others
            color = (0, 255, 0) if is_target else (0, 0, 255)
            
            # Draw bounding box
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            tag = f"{label} {conf:.2f}"
            (tw, th), _ = cv2.getTextSize(tag, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
            ty = max(y1 - 4, th + 4)
            cv2.rectangle(overlay, (x1, ty - th - 4), (x1 + tw + 4, ty), color, -1)
            cv2.putText(overlay, tag, (x1 + 2, ty - 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)
        
        # Draw UI info
        found_count = sum(1 for t in targets if t["found"])
        total_count = len(targets)
        
        cv2.putText(overlay, f"Scavenger Hunt - Language: {self.target_language.upper()}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)
        cv2.putText(overlay, f"Found: {found_count}/{total_count}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)
        cv2.putText(overlay, "Press 'q' to quit game", (10, overlay.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)
        
        # Draw target items list on the right side
        y_offset = 30
        cv2.putText(overlay, "Targets:", (overlay.shape[1] - 200, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        y_offset += 25
        for target in targets:
            status = "✅" if target["found"] else "⬜"
            color = (0, 255, 0) if target["found"] else (255, 255, 255)
            cv2.putText(overlay, f"{status} {target['translated']}", 
                       (overlay.shape[1] - 200, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
            y_offset += 20
        
        return overlay
    
    def start_detection(self, targets, callback=None):
        """Start continuous detection with display window"""
        self.running = True
        self.targets = targets
        self.detection_thread = threading.Thread(target=self._detection_loop, args=(callback,))
        self.detection_thread.daemon = True  # Make thread daemon so it exits when main thread exits
        self.detection_thread.start()
        return True
    
    def _detection_loop(self, callback):
        """Main detection loop with display window"""
        # Open camera
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            print("❌ Cannot open camera")
            self.running = False
            return
        
        print(f"🎯 Scavenger hunt detection started. Looking for items in {self.target_language}")
        print(f"📹 Webcam window opening... Press 'q' in the webcam window to quit.")
        
        frame_count = 0
        last_detections = []
        
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to read frame")
                break
            
            # Run detection every 3 frames
            if frame_count % 3 == 0:
                results = self.model(frame, conf=self.conf, verbose=False)
                
                # Parse detections
                detections = []
                for result in results:
                    if result.boxes is not None:
                        for box in result.boxes:
                            x1, y1, x2, y2 = box.xyxy[0].tolist()
                            conf = float(box.conf[0])
                            cls = int(box.cls[0])
                            label_en = result.names[cls]
                            label_translated = self.translate_label(label_en)
                            
                            detections.append({
                                "label_en": label_en,
                                "label": label_translated,
                                "confidence": conf,
                                "bbox": [int(x1), int(y1), int(x2 - x1), int(y2 - y1)]
                            })
                
                last_detections = detections
                self.current_detections = detections
                
                # Call callback with detections to update game state
                if callback and self.running:
                    callback(detections)
            
            # Draw detections on frame
            display_frame = self.draw_detections(frame, last_detections, self.targets)
            
            # Show the window
            cv2.imshow(self.window_name, display_frame)
            
            # Check for key press (non-blocking)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:  # 'q' or ESC
                print("📷 User pressed 'q', stopping scavenger hunt...")
                self.running = False
                break
            
            frame_count += 1
            time.sleep(0.03)  # ~30 FPS
        
        # Cleanup
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        print("📷 Scavenger hunt detection stopped")
    
    def stop_detection(self):
        """Stop the detection thread"""
        self.running = False
        if hasattr(self, 'cap') and self.cap:
            self.cap.release()
        cv2.destroyAllWindows()

# Global instance
detector = None