"""
webcam_tester.py

Webcam testing module for Ultralytics YOLO models (v8/v11).

Usage:
    from webcam_tester import YOLOWebcamTester

    # Pass a path to your .onnx file
    YOLOWebcamTester("your_model.onnx", conf=0.4).run()

    # Or pass a pre-loaded model
    from ultralytics import YOLO
    model = YOLO("your_model.onnx")
    YOLOWebcamTester(model, conf=0.4).run()
"""

import sys
import cv2
import numpy as np



class YOLOWebcamTester:
    """
    Captures webcam frames and runs them through an Ultralytics YOLO model.

    Args:
        model:        A loaded ultralytics.YOLO instance, or a path string to
                      a .onnx / .pt weights file.
        conf:         Confidence threshold (default 0.25).
        iou:          IoU threshold for NMS (default 0.45).
        camera_index: Webcam device index (default 0).
        window_name:  Display window title.
    """

    def __init__(
        self,
        model,
        conf: float = 0.25,
        iou: float = 0.45,
        camera_index: int = 0,
        window_name: str = "YOLO Webcam Tester",
    ):
        if isinstance(model, (str, bytes)):
            from ultralytics import YOLO
            model = YOLO(model)
        self.model = model
        self.conf = conf
        self.iou = iou
        self.camera_index = camera_index
        self.window_name = window_name

    def _infer(self, frame: np.ndarray) -> list:
        """Run inference and return a list of box dicts."""
        results = self.model(frame, conf=self.conf, iou=self.iou, verbose=False)
        boxes = []
        for result in results:
            names = result.names
            for box in result.boxes:
                xyxy = box.xyxy[0].tolist()
                boxes.append({
                    "x1": xyxy[0], "y1": xyxy[1],
                    "x2": xyxy[2], "y2": xyxy[3],
                    "label": names.get(int(box.cls[0]), str(int(box.cls[0]))),
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
        cv2.putText(overlay, f"Detections: {len(boxes)}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 255), 2)
        cv2.putText(overlay, "q/Esc: quit   s: snapshot",
                    (10, overlay.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)
        return overlay

    @staticmethod
    def _class_colour(label: str) -> tuple:
        h = hash(label) & 0xFFFFFF
        return (h & 0xFF, (h >> 8) & 0xFF, (h >> 16) & 0xFF)

    def run(self, skip_frames: int = 0) -> None:
        """
        Open the webcam and start the inference loop.

        Args:
            skip_frames: Run the model every (skip_frames+1) frames to reduce load.

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

        print(f"[YOLOWebcamTester] Camera {self.camera_index} opened. Press 'q' to quit.")
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
                    cv2.imwrite("snapshot.png", display)
                    print("[YOLOWebcamTester] Snapshot saved → snapshot.png")
        finally:
            cap.release()
            cv2.destroyAllWindows()
            print("[YOLOWebcamTester] Camera released.")

    def capture_single_frame(self) -> np.ndarray:
        """Capture and return a single BGR frame without opening a window."""
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open camera index {self.camera_index}.")
        ret, frame = cap.read()
        cap.release()
        if not ret:
            raise RuntimeError("Failed to capture frame.")
        return frame


# ---------------------------------------------------------------------------
# Entry point:  python webcam_tester.py your_model.onnx
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    weights = sys.argv[1] if len(sys.argv) > 1 else "yolov8n.pt"
    print(f"Loading {weights} …")
    YOLOWebcamTester(weights, conf=0.35).run()

