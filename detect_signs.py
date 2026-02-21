import cv2
import mediapipe as mp
import numpy as np
import pickle
import threading
import time
import os


class Detector:
    """Encapsulates webcam + MediaPipe detection and exposes a frame generator and state.

    Use the same model and landmark processing as the original `detect_signs.py`.
    """

    def __init__(self, model_path='sign_classifier.p', sign_names=None, camera_index=0):
        self.model_path = model_path
        
        self.SIGN_NAMES = sign_names or [
            "hello", "thanks", "yes", "no", "iloveyou",
            'a','b','c','d','e','f','g','h','i','j','k','l','m',
            'n','o','p','r','s','t','u','v','w','x','y','z'
        ]

        # Filipino translations for signs
        self.FILIPINO_TRANSLATIONS = {
            "hello": "kumusta",
            "thanks": "salamat",
            "yes": "oo",
            "no": "hindi",
            "iloveyou": "mahal kita"
        }

        # Load model if available
        self.model = None
        self.scaler = None
        if os.path.exists(self.model_path):
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
                # Handle both old format (just model) and new format (model + scaler)
                if isinstance(model_data, dict):
                    self.model = model_data.get('model')
                    self.scaler = model_data.get('scaler')
                else:
                    self.model = model_data
                    self.scaler = None
                print(f"[Detector] Model loaded successfully from {self.model_path}")
        else:
            print(f"[Detector] WARNING: Model file not found at {self.model_path}")

        # MediaPipe setup (optimized thresholds for faster detection)
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            model_complexity=0,
            min_detection_confidence=0.6,  
            min_tracking_confidence=0.6,   
            max_num_hands=1  
        )

        # Camera setup with optimized settings
        self.camera = cv2.VideoCapture(camera_index)
        
        self.ret = False
        self.frame = None
        self._running = True 
        self._lock = threading.Lock()
        
        # Detection state - initialize BEFORE starting thread
        self.detection_history = []
        self.MAX_HISTORY = 20
        self.latest_detection = {"sign": None, "conf": 0.0, "timestamp": None}
        
        # Frame processing control: only run heavy detection every Nth frame
        self.frame_count = 0
        self.process_every = 2
        
        if not self.camera.isOpened():
            print(f"[Detector] ERROR: Could not open camera with index {camera_index}")
        else:
            # Balance resolution and FPS for accuracy on low-CPU systems (e.g., Intel i3)
            # 480x360 gives better landmark detection than 320x240
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
            self.camera.set(cv2.CAP_PROP_FPS, 20)
            print(f"[Detector] Camera opened successfully with index {camera_index}")

        # Start background thread AFTER all initialization is complete
        threading.Thread(target=self._update_frame, daemon=True).start()
        
        # Pre-warm the camera to ensure frames are ready immediately
        self._warmup_camera()

    def _warmup_camera(self):
        """Warm up the camera by waiting for initial frames in background"""
        def warmup():
            try:
                print("[Detector] Warming up camera...")
                wait_count = 0
                max_wait = 100  # Wait up to 5 seconds
                while wait_count < max_wait:
                    if self.ret and self.frame is not None:
                        print(f"[Detector] Camera warmed up! Got first frame in {wait_count * 0.05:.1f}s")
                        return
                    time.sleep(0.05)
                    wait_count += 1
                if wait_count >= max_wait:
                    print("[Detector] WARNING: Camera warmup timeout - no frames received within 5 seconds")
            except Exception as e:
                print(f"[Detector] Camera warmup error: {e}")
        
        threading.Thread(target=warmup, daemon=True).start()

    def _update_frame(self):
        """Background thread to continuously read frames from the camera."""
        if not self.camera.isOpened():
            print("[Detector] ERROR: Camera not opened in _update_frame, cannot read frames")
            return
        
        frame_read_count = 0
        frame_fail_count = 0
        last_log = time.time()
        consecutive_failures = 0
        
        while self._running:
            try:
                success, frame = self.camera.read()
                if success:
                    self.ret = True
                    self.frame = frame
                    frame_read_count += 1
                    consecutive_failures = 0  # Reset on success
                    
                    # Log every few seconds
                    if time.time() - last_log > 3:
                        print(f"[Detector] Frame reader active: {frame_read_count} frames read, {frame_fail_count} failures")
                        last_log = time.time()
                else:
                    consecutive_failures += 1
                    frame_fail_count += 1
                    self.ret = False
                    
                    # Log failures periodically, not every time
                    if consecutive_failures == 1 or consecutive_failures % 30 == 0:
                        print(f"[Detector] WARNING: Failed to read frame from camera (consecutive: {consecutive_failures})")
                    
                    # Small delay on failure to prevent CPU hammering
                    time.sleep(0.01)
                    
                    # If we have too many consecutive failures, try to recover
                    if consecutive_failures > 50:
                        print("[Detector] CRITICAL: Camera read failed 50+ times, attempting recovery...")
                        try:
                            self.camera.release()
                            time.sleep(0.5)  # Give camera time to fully close
                            self.camera = cv2.VideoCapture(0)
                            time.sleep(0.5)  # Give camera time to open
                            if self.camera.isOpened():
                                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
                                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
                                self.camera.set(cv2.CAP_PROP_FPS, 20)
                                print("[Detector] Camera recovery completed successfully")
                                consecutive_failures = 0
                            else:
                                print("[Detector] Camera recovery failed - camera could not be reopened")
                        except Exception as e:
                            print(f"[Detector] Camera recovery error: {e}")
                    
            except Exception as e:
                print(f"[Detector] Exception in frame reader: {e}")
                self.ret = False
                consecutive_failures += 1
                time.sleep(0.01)

    def reload_model(self):
        #Retraining without restarting the app
        if os.path.exists(self.model_path):
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)

    def get_latest(self):
        with self._lock:
            detection = dict(self.latest_detection)
            if detection["sign"] and detection["sign"] in self.FILIPINO_TRANSLATIONS:
                detection["filipino"] = self.FILIPINO_TRANSLATIONS[detection["sign"]]
            else:
                detection["filipino"] = detection["sign"]  # fallback to original for letters
            return detection

    def get_history(self):
        with self._lock:
            return list(self.detection_history)

    def stop(self):
        self._running = False

    def release(self):
        try:
            self.camera.release()
        except Exception:
            pass
        try:
            self.hands.close()
        except Exception:
            pass

    def _process_frame(self, frame):
        """Run a lightweight processing pass. Heavy MediaPipe/model prediction runs only every `process_every` frames.

        This reduces CPU usage on low-power machines by skipping full detection on most frames.
        """
        # Mirror frame for user-facing orientation
        image = cv2.flip(frame, 1)

        # Overlay last known detection immediately to keep feed responsive
        if self.latest_detection["sign"]:
            text = f'{self.latest_detection["sign"]} ({int(self.latest_detection["conf"]*100)}%)'
            cv2.putText(image, text, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 3)
            cv2.putText(image, text, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 1)
            if self.latest_detection["sign"] in self.FILIPINO_TRANSLATIONS:
                filipino_text = self.FILIPINO_TRANSLATIONS[self.latest_detection["sign"]]
                cv2.putText(image, filipino_text, (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
                cv2.putText(image, filipino_text, (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 1)

        # Decide whether to run heavy detection on this frame
        self.frame_count = (self.frame_count + 1) % self.process_every
        if self.frame_count != 0:
            # return quickly without running MediaPipe/model
            return image

        # Run detection on a downscaled RGB copy to save CPU
        small = cv2.resize(image, (240, 180))
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)

        sign = None
        conf = 0.0

        if results and results.multi_hand_landmarks and self.model is not None:
            # Use the first hand found; scale landmarks back to original coordinates if needed
            hand_landmarks = results.multi_hand_landmarks[0]
            # Draw landmarks on full-size image for visibility
            self.mp_drawing.draw_landmarks(image, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

            landmarks = []
            for lm in hand_landmarks.landmark:
                landmarks.extend([lm.x, lm.y, lm.z])

            if len(landmarks) >= 63:
                try:
                    landmarks_array = np.array(landmarks).reshape(1, -1)
                    if self.scaler is not None:
                        landmarks_array = self.scaler.transform(landmarks_array)
                    pred = self.model.predict(landmarks_array)
                    probs = self.model.predict_proba(landmarks_array)
                    conf = float(np.max(probs))
                    sign = self.SIGN_NAMES[int(pred[0])]
                except Exception as e:
                    print(f"[Detector] Prediction error: {e}")
                    sign = None
                    conf = 0.0

        # Update state if confident (lowered threshold to 0.4 for better recall)
        if sign is not None and conf >= 0.6:
            ts = time.time()
            with self._lock:
                if not self.detection_history or self.detection_history[-1]["sign"] != sign:
                    self.detection_history.append({"sign": sign, "conf": conf, "ts": ts})
                    if len(self.detection_history) > self.MAX_HISTORY:
                        self.detection_history.pop(0)
                self.latest_detection.update({"sign": sign, "conf": conf, "timestamp": ts})
                print(f"[Detector] Detected: {sign} ({conf*100:.1f}%)")
        else:
            # Clear detection if no hand or low confidence
            with self._lock:
                self.latest_detection.update({"sign": None, "conf": 0.0, "timestamp": None})

        return image

    def generate_frames(self):
        """Yield multipart JPEG frames for MJPEG streaming (for Flask `/video_feed`)."""
        print("[Detector] generate_frames() started")
        frame_count = 0
        last_log = time.time()
        init_wait_count = 0
        max_init_wait = 50  # Wait up to 2.5 seconds for initial frame
        
        while self._running:
            # Use the latest frame grabbed by the background reader thread
            if not self.ret or self.frame is None:
                init_wait_count += 1
                if init_wait_count <= max_init_wait:
                    print(f"[Detector] Waiting for camera frame... ({init_wait_count}/{max_init_wait})")
                time.sleep(0.05)
                continue
            
            init_wait_count = 0
            # copy to avoid race conditions
            frame = self.frame.copy()
            image = self._process_frame(frame)

            # Lower JPEG quality (60) for faster encoding and reduced latency
            ret, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 75])
            if not ret:
                continue
            frame_count += 1
            if time.time() - last_log > 3:
                print(f"[Detector] generate_frames yielding: {frame_count} frames sent")
                last_log = time.time()
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    def run_window(self):
        """Run the original OpenCV window UI (for local desktop usage)."""
        BUTTON_TEXT = "Quit"
        BUTTON_POS = (10, 350)
        BUTTON_WIDTH, BUTTON_HEIGHT = 100, 40
        BUTTON_COLOR = (0, 0, 0)
        BUTTON_TEXT_COLOR = (255, 255, 255)

        def mouse_click(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                if (BUTTON_POS[0] <= x <= BUTTON_POS[0] + BUTTON_WIDTH and
                        BUTTON_POS[1] <= y <= BUTTON_POS[1] + BUTTON_HEIGHT):
                    with self._lock:
                        self.detection_history = []
                    print("Quit button clicked. Exiting...")

        cv2.namedWindow('Sign Language Detector')
        cv2.setMouseCallback('Sign Language Detector', mouse_click)

        while True:
            success, frame = self.camera.read()
            if not success:
                break

            image = self._process_frame(frame)

            # Draw the Quit button and instructions
            cv2.rectangle(image, BUTTON_POS, (BUTTON_POS[0] + BUTTON_WIDTH, BUTTON_POS[1] + BUTTON_HEIGHT), BUTTON_COLOR, -1)
            cv2.putText(image, BUTTON_TEXT, (BUTTON_POS[0] + 12, BUTTON_POS[1] + 27), cv2.FONT_HERSHEY_SIMPLEX, 0.7, BUTTON_TEXT_COLOR, 2)
            cv2.putText(image, "Show a sign to the camera", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 3)
            cv2.putText(image, "Show a sign to the camera", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)

            # Display Detection History
            with self._lock:
                history_text = "History: " + " -> ".join([h["sign"] for h in self.detection_history])
            cv2.putText(image, history_text, (10, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)

            cv2.imshow('Sign Language Detector', image)

            if cv2.waitKey(5) & 0xFF == ord('q'):
                break

        self.release()


if __name__ == '__main__':
    d = Detector()
    try:
        d.run_window()
    except KeyboardInterrupt:
        pass
cv2.destroyAllWindows()