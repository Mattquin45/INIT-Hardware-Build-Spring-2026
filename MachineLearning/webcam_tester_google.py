# # webcam_tester_translate.py

# import sys
# import cv2
# import numpy as np
# from google.cloud import translate_v2 as translate
# import time

# # Initialize Google Translate client
# translate_client = translate.Client()

# def translate_label(label: str, target_language: str = "es", cache: dict = None) -> str:
#     #Translate a YOLO class label to the target language with caching."""
#     if cache is None:
#         cache = {}
#     if label in cache:
#         return cache[label]
#     result = translate_client.translate(label, target_language=target_language)
#     translated = result["translatedText"]
#     cache[label] = translated
#     return translated


# class YOLOWebcamTester:
#     """
#     Captures webcam frames and runs them through an Ultralytics YOLO model
#     with optional translation of detected labels.
#     """

#     def __init__(
#         self,
#         model,
#         conf: float = 0.25,
#         iou: float = 0.45,
#         camera_index: int = 0,
#         window_name: str = "YOLO Webcam Tester",
#         target_language: str = "es",
#     ):
#         if isinstance(model, (str, bytes)):
#             from ultralytics import YOLO
#             model = YOLO(model)
#         self.model = model
#         self.conf = conf
#         self.iou = iou
#         self.camera_index = camera_index
#         self.window_name = window_name
#         self.target_language = target_language
#         self.label_cache = {}  # for caching translations

#     def _infer(self, frame: np.ndarray) -> list:
#         """Run inference and return a list of box dicts."""
#         results = self.model(frame, conf=self.conf, iou=self.iou, verbose=False)
#         boxes = []
#         for result in results:
#             names = result.names
#             for box in result.boxes:
#                 xyxy = box.xyxy[0].tolist()
#                 label_en = names.get(int(box.cls[0]), str(int(box.cls[0])))
#                 # Translate label with caching
#                 label_translated = translate_label(label_en, self.target_language, self.label_cache)
#                 boxes.append({
#                     "x1": xyxy[0], "y1": xyxy[1],
#                     "x2": xyxy[2], "y2": xyxy[3],
#                     "label": label_translated,
#                     "confidence": float(box.conf[0]),
#                 })
#         return boxes

#     def _draw(self, frame: np.ndarray, boxes: list) -> np.ndarray:
#         overlay = frame.copy()
#         for box in boxes:
#             x1, y1, x2, y2 = int(box["x1"]), int(box["y1"]), int(box["x2"]), int(box["y2"])
#             colour = self._class_colour(box["label"])
#             cv2.rectangle(overlay, (x1, y1), (x2, y2), colour, 2)
#             tag = f"{box['label']} {box['confidence']:.2f}"
#             (tw, th), _ = cv2.getTextSize(tag, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
#             ty = max(y1 - 4, th + 4)
#             cv2.rectangle(overlay, (x1, ty - th - 4), (x1 + tw + 4, ty), colour, -1)
#             cv2.putText(overlay, tag, (x1 + 2, ty - 2),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)
#         cv2.putText(overlay, f"Detections: {len(boxes)}", (10, 30),
#                     cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 255), 2)
#         cv2.putText(overlay, "q/Esc: quit   s: snapshot",
#                     (10, overlay.shape[0] - 10),
#                     cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)
#         return overlay

#     @staticmethod
#     def _class_colour(label: str) -> tuple:
#         h = hash(label) & 0xFFFFFF
#         return (h & 0xFF, (h >> 8) & 0xFF, (h >> 16) & 0xFF)

#     def run(self, skip_frames: int = 0) -> None:
#         cap = cv2.VideoCapture(self.camera_index)
#         if not cap.isOpened():
#             raise RuntimeError(f"Cannot open camera index {self.camera_index}.")
#         time.sleep(2)

#         print(f"[YOLOWebcamTester] Camera {self.camera_index} opened. Press 'q' to quit.")
#         frame_count = 0
#         last_boxes: list = []

#         try:
#             while True:
#                 ret, frame = cap.read()
#                 if not ret:
#                     print("[YOLOWebcamTester] Failed to read frame. Exiting.")
#                     break

#                 frame_count += 1
#                 if frame_count % (skip_frames + 1) == 0:
#                     try:
#                         last_boxes = self._infer(frame)
#                     except Exception as exc:
#                         print(f"[YOLOWebcamTester] Inference error: {exc}")

#                 display = self._draw(frame, last_boxes)
#                 cv2.imshow(self.window_name, display)

#                 key = cv2.waitKey(1) & 0xFF
#                 if key in (ord("q"), 27):
#                     break
#                 if key == ord("s"):
#                     cv2.imwrite("snapshot.png", display)
#                     print("[YOLOWebcamTester] Snapshot saved → snapshot.png")
#         finally:
#             cap.release()
#             cv2.destroyAllWindows()
#             print("[YOLOWebcamTester] Camera released.")

#     def capture_single_frame(self) -> np.ndarray:
#         cap = cv2.VideoCapture(self.camera_index)
#         if not cap.isOpened():
#             raise RuntimeError(f"Cannot open camera index {self.camera_index}.")
#         ret, frame = cap.read()
#         cap.release()
#         if not ret:
#             raise RuntimeError("Failed to capture frame.")
#         return frame



# # Entry point: python webcam_tester_translate.py your_model.onnx
# # ---------------------------------------------------------------------------
# if __name__ == "__main__":
#     weights = sys.argv[1] if len(sys.argv) > 1 else "yolov8n.pt"
#     print(f"Loading {weights} …")
#     YOLOWebcamTester(weights, conf=0.35, target_language="es").run()


# webcam_tester_google.py

import sys
import cv2
import numpy as np
from google.cloud import translate_v2 as translate
import time
import argparse

# Initialize Google Translate client
translate_client = translate.Client()

def translate_label(label: str, target_language: str = "es", cache: dict = None) -> str:
    """Translate a YOLO class label to the target language with caching."""
    if cache is None:
        cache = {}
    if label in cache:
        return cache[label]
    try:
        result = translate_client.translate(label, target_language=target_language)
        translated = result["translatedText"]
        cache[label] = translated
        return translated
    except Exception as e:
        print(f"Translation error for '{label}': {e}")
        return label  # Return original label if translation fails


class YOLOWebcamTester:
    """
    Captures webcam frames and runs them through an Ultralytics YOLO model
    with optional translation of detected labels.
    """

    def __init__(
        self,
        model,
        conf: float = 0.25,
        iou: float = 0.45,
        camera_index: int = 0,
        window_name: str = "YOLO Webcam Tester",
        target_language: str = "es",
    ):
        if isinstance(model, (str, bytes)):
            from ultralytics import YOLO
            model = YOLO(model)
        self.model = model
        self.conf = conf
        self.iou = iou
        self.camera_index = camera_index
        self.window_name = window_name
        self.target_language = target_language
        self.label_cache = {}  # for caching translations

    def _infer(self, frame: np.ndarray) -> list:
        """Run inference and return a list of box dicts."""
        results = self.model(frame, conf=self.conf, iou=self.iou, verbose=False)
        boxes = []
        for result in results:
            names = result.names
            for box in result.boxes:
                xyxy = box.xyxy[0].tolist()
                label_en = names.get(int(box.cls[0]), str(int(box.cls[0])))
                # Translate label with caching
                label_translated = translate_label(label_en, self.target_language, self.label_cache)
                boxes.append({
                    "x1": xyxy[0], "y1": xyxy[1],
                    "x2": xyxy[2], "y2": xyxy[3],
                    "label": label_translated,
                    "confidence": float(box.conf[0]),
                })
        return boxes

    def _draw(self, frame: np.ndarray, boxes: list) -> np.ndarray:
        overlay = frame.copy()
        for box in boxes:
            x1, y1, x2, y2 = int(box["x1"]), int(box["y1"]), int(box["x2"]), int(box["y2"])
            colour = self._class_colour(box["label"])
            cv2.rectangle(overlay, (x1, y1), (x2, y2), colour, 2)
            tag = f"{box['label']} {box['confidence']:.2f}"
            (tw, th), _ = cv2.getTextSize(tag, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
            ty = max(y1 - 4, th + 4)
            cv2.rectangle(overlay, (x1, ty - th - 4), (x1 + tw + 4, ty), colour, -1)
            cv2.putText(overlay, tag, (x1 + 2, ty - 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)
        
        # Display current language
        cv2.putText(overlay, f"Language: {self.target_language.upper()}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)
        cv2.putText(overlay, f"Detections: {len(boxes)}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)
        cv2.putText(overlay, "q/Esc: quit   s: snapshot",
                    (10, overlay.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)
        return overlay

    @staticmethod
    def _class_colour(label: str) -> tuple:
        h = hash(label) & 0xFFFFFF
        return (h & 0xFF, (h >> 8) & 0xFF, (h >> 16) & 0xFF)

    def run(self, skip_frames: int = 0) -> None:
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open camera index {self.camera_index}.")
        time.sleep(2)

        print(f"[YOLOWebcamTester] Camera {self.camera_index} opened. Language: {self.target_language}")
        print(f"[YOLOWebcamTester] Press 'q' to quit, 's' to save snapshot.")
        
        frame_count = 0
        last_boxes: list = []

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("[YOLOWebcamTester] Failed to read frame. Exiting.")
                    break

                frame_count += 1
                if frame_count % (skip_frames + 1) == 0:
                    try:
                        last_boxes = self._infer(frame)
                    except Exception as exc:
                        print(f"[YOLOWebcamTester] Inference error: {exc}")

                display = self._draw(frame, last_boxes)
                cv2.imshow(self.window_name, display)

                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), 27):
                    break
                if key == ord("s"):
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    filename = f"snapshot_{timestamp}.png"
                    cv2.imwrite(filename, display)
                    print(f"[YOLOWebcamTester] Snapshot saved → {filename}")
        finally:
            cap.release()
            cv2.destroyAllWindows()
            print("[YOLOWebcamTester] Camera released.")

    def capture_single_frame(self) -> np.ndarray:
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open camera index {self.camera_index}.")
        ret, frame = cap.read()
        cap.release()
        if not ret:
            raise RuntimeError("Failed to capture frame.")
        return frame


# Entry point with argument parsing
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='YOLO Webcam Tester with Translation')
    parser.add_argument('model', nargs='?', default='yolov8n.pt', 
                       help='Path to YOLO model file (default: yolov8n.pt)')
    parser.add_argument('--conf', type=float, default=0.35,
                       help='Confidence threshold (default: 0.35)')
    parser.add_argument('--iou', type=float, default=0.45,
                       help='IOU threshold (default: 0.45)')
    parser.add_argument('--camera', type=int, default=0,
                       help='Camera index (default: 0)')
    parser.add_argument('--lang', type=str, default='es',
                       help='Target language code (default: es)')
    
    args = parser.parse_args()
    
    print(f"Loading model: {args.model}")
    print(f"Target language: {args.lang}")
    print(f"Confidence threshold: {args.conf}")
    
    try:
        YOLOWebcamTester(
            args.model, 
            conf=args.conf, 
            iou=args.iou,
            camera_index=args.camera,
            target_language=args.lang
        ).run()
    except KeyboardInterrupt:
        print("\n[YOLOWebcamTester] Interrupted by user.")
    except Exception as e:
        print(f"[YOLOWebcamTester] Error: {e}")
        sys.exit(1)