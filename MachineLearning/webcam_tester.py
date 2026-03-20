"""
webcam_tester.py

Webcam testing module for image recognition models.
Includes native support for Ultralytics YOLO (v8/v11).

--- Quick start with YOLO ---
    from ultralytics import YOLO
    from webcam_tester import YOLOWebcamTester

    model = YOLO("yolov8n.pt")          # or any .pt / .onnx weights
    YOLOWebcamTester(model).run()

--- Generic model usage ---
    from webcam_tester import WebcamTester

    def my_model(frame):
        # frame: BGR numpy array (H x W x 3)
        return {
            'label': 'cat',
            'confidence': 0.95,
            'boxes': [{'x1':10,'y1':20,'x2':100,'y2':150,
                       'label':'cat','confidence':0.95}]
        }

    WebcamTester(model_fn=my_model).run()
"""

import cv2
import numpy as np
from typing import Callable, Optional


# ---------------------------------------------------------------------------
# Generic tester
# ---------------------------------------------------------------------------

class WebcamTester:
    """
    Captures frames from a webcam and runs them through a provided model function.

    Args:
        model_fn:      Callable(frame: ndarray) -> dict with optional keys:
                         'label' (str), 'confidence' (float 0-1),
                         'boxes' (list of dicts with 'x1','y1','x2','y2',
                                  optionally 'label','confidence')
        camera_index:  cv2.VideoCapture device index (default 0).
        window_name:   Display window title.
        preprocess_fn: Optional callable applied to each frame before model_fn.
    """

    def __init__(
        self,
        model_fn: Callable[[np.ndarray], dict],
        camera_index: int = 0,
        window_name: str = "Webcam Model Tester",
        preprocess_fn: Optional[Callable[[np.ndarray], np.ndarray]] = None,
    ):
        self.model_fn = model_fn
        self.camera_index = camera_index
        self.window_name = window_name
        self.preprocess_fn = preprocess_fn

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def _draw_results(self, frame: np.ndarray, results: dict) -> np.ndarray:
        overlay = frame.copy()

        for box in results.get("boxes", []):
            x1, y1, x2, y2 = int(box["x1"]), int(box["y1"]), int(box["x2"]), int(box["y2"])
            cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 0), 2)
            text = box.get("label", "")
            conf = box.get("confidence")
            if conf is not None:
                text = f"{text} {conf:.2f}" if text else f"{conf:.2f}"
            if text:
                cv2.putText(overlay, text, (x1, max(y1 - 8, 12)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)

        label = results.get("label", "")
        conf  = results.get("confidence")
        if label or conf is not None:
            text = f"{label}  {conf:.2%}" if (label and conf is not None) \
                   else label or f"{conf:.2%}"
            cv2.putText(overlay, text, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 200, 255), 2)

        return overlay

    @staticmethod
    def _draw_hint(frame: np.ndarray) -> None:
        cv2.putText(frame, "q/Esc: quit   s: snapshot",
                    (10, frame.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, skip_frames: int = 0) -> None:
        """
        Open webcam and run the inference loop.

        Args:
            skip_frames: Run the model every (skip_frames+1) frames.
                         Useful to reduce CPU/GPU load (e.g. skip_frames=1
                         means run on every other frame).

        Keyboard shortcuts:
            q / Esc  – quit
            s        – save snapshot to snapshot.png
        """
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            raise RuntimeError(
                f"Cannot open camera index {self.camera_index}. "
                "Ensure the webcam is connected and not used by another app."
            )

        print(f"[WebcamTester] Camera {self.camera_index} opened. Press 'q' to quit.")
        frame_count  = 0
        last_results: dict = {}

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("[WebcamTester] Failed to read frame. Exiting.")
                    break

                frame_count += 1
                if frame_count % (skip_frames + 1) == 0:
                    inp = self.preprocess_fn(frame) if self.preprocess_fn else frame
                    try:
                        last_results = self.model_fn(inp) or {}
                    except Exception as exc:
                        last_results = {"label": f"Error: {exc}"}

                display = self._draw_results(frame, last_results)
                self._draw_hint(display)
                cv2.imshow(self.window_name, display)

                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), 27):
                    break
                if key == ord("s"):
                    cv2.imwrite("snapshot.png", display)
                    print("[WebcamTester] Snapshot saved → snapshot.png")
        finally:
            cap.release()
            cv2.destroyAllWindows()
            print("[WebcamTester] Camera released.")

    def capture_single_frame(self) -> np.ndarray:
        """Return a single BGR frame from the webcam without opening a window."""
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open camera index {self.camera_index}.")
        ret, frame = cap.read()
        cap.release()
        if not ret:
            raise RuntimeError("Failed to capture frame.")
        return frame


# ---------------------------------------------------------------------------
# Ultralytics YOLO tester
# ---------------------------------------------------------------------------

class YOLOWebcamTester(WebcamTester):
    """
    Webcam tester with built-in support for Ultralytics YOLO models (v8/v11).

    Args:
        model:        A loaded ultralytics.YOLO instance, or a path string to
                      a .onnx / .pt weights file.
        conf:         Confidence threshold (default 0.25).
        iou:          IoU threshold for NMS (default 0.45).
        camera_index: Webcam device index (default 0).
        window_name:  Display window title.

    Example:
        from webcam_tester import YOLOWebcamTester

        # Load directly from an ONNX file
        YOLOWebcamTester("yolov8n.onnx", conf=0.4).run()

        # Or pass a pre-loaded model
        from ultralytics import YOLO
        model = YOLO("yolov8n.onnx")
        YOLOWebcamTester(model, conf=0.4).run()
    """

    def __init__(
        self,
        model,
        conf: float = 0.25,
        iou:  float = 0.45,
        camera_index: int = 0,
        window_name: str = "YOLO Webcam Tester",
    ):
        if isinstance(model, (str, bytes)):
            from ultralytics import YOLO
            model = YOLO(model)
        self.yolo_model = model
        self.conf = conf
        self.iou  = iou
        super().__init__(
            model_fn=self._run_yolo,
            camera_index=camera_index,
            window_name=window_name,
        )

    def _run_yolo(self, frame: np.ndarray) -> dict:
        """Run YOLO inference and convert results to the standard dict format."""
        results = self.yolo_model(frame, conf=self.conf, iou=self.iou, verbose=False)
        boxes = []

        for result in results:
            names = result.names  # {class_id: class_name}
            for box in result.boxes:
                xyxy  = box.xyxy[0].tolist()   # [x1, y1, x2, y2]
                conf  = float(box.conf[0])
                cls   = int(box.cls[0])
                label = names.get(cls, str(cls))
                boxes.append({
                    "x1": xyxy[0], "y1": xyxy[1],
                    "x2": xyxy[2], "y2": xyxy[3],
                    "label": label,
                    "confidence": conf,
                })

        return {"boxes": boxes}

    def _draw_results(self, frame: np.ndarray, results: dict) -> np.ndarray:
        """Draw YOLO boxes with class-specific colours."""
        overlay = frame.copy()

        for box in results.get("boxes", []):
            x1, y1, x2, y2 = int(box["x1"]), int(box["y1"]), int(box["x2"]), int(box["y2"])
            label = box.get("label", "")
            conf  = box.get("confidence", 0.0)

            # Deterministic colour per class name
            colour = self._class_colour(label)
            cv2.rectangle(overlay, (x1, y1), (x2, y2), colour, 2)

            tag = f"{label} {conf:.2f}"
            (tw, th), _ = cv2.getTextSize(tag, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
            ty = max(y1 - 4, th + 4)
            cv2.rectangle(overlay, (x1, ty - th - 4), (x1 + tw + 4, ty), colour, -1)
            cv2.putText(overlay, tag, (x1 + 2, ty - 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)

        # Detection count
        n = len(results.get("boxes", []))
        cv2.putText(overlay, f"Detections: {n}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 255), 2)

        return overlay

    @staticmethod
    def _class_colour(label: str) -> tuple:
        """Return a consistent BGR colour for a given class label."""
        h = hash(label) & 0xFFFFFF
        return (h & 0xFF, (h >> 8) & 0xFF, (h >> 16) & 0xFF)


# ---------------------------------------------------------------------------
# Demo – runs when executed directly
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    try:
        # Pass a path as a CLI argument, e.g.:  python webcam_tester.py model.onnx
        weights = sys.argv[1] if len(sys.argv) > 1 else "yolov8n.pt"
        print(f"Loading {weights} …")
        YOLOWebcamTester(weights, conf=0.35).run()
    except ImportError:
        print("ultralytics not installed. Running generic dummy demo instead.")
        print("Install with:  pip install ultralytics")

        def dummy_model(frame: np.ndarray) -> dict:
            mean = frame.mean(axis=(0, 1)).astype(int)
            return {"label": f"B={mean[0]} G={mean[1]} R={mean[2]}"}

        WebcamTester(model_fn=dummy_model).run()
