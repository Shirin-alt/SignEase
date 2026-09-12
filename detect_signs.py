import cv2
import mediapipe as mp
import numpy as np
import pickle
import threading
import time
import os
import torch
import torch.nn as nn


class Detector:

    def __init__(self, model_path='sign_classifier.p', sign_names=None, camera_index=0):
        self.model_path = model_path

        self.SIGN_NAMES = sign_names or [
            'a','b','c','d','e','f','g','h','i','j','k','l','m',
            'n','o','p','q','r','s','t','u','v','w','x','y','z'
        ]

        self.FILIPINO_TRANSLATIONS = {
            'hi':              'Kumusta',
            'good_morning':    'Magandang Umaga',
            'good_afternoon':  'Magandang Hapon',
            'good_evening':    'Magandang Gabi',
            'how_are_you':     'Kumusta ka?',
            'i_am_fine':       'Mabuti naman ako',
            'i_am_not_fine':   'Hindi ako mabuti',
            'whats_your_name': 'Ano ang pangalan mo?',
            'my_name_is':      'Ang pangalan ko ay...',
            'sorry':           'Pasensya na',
            'thank_you':       'Salamat',
        }

        self.PHRASE_DISPLAY = {
            'hi':              'Hi',
            'good_morning':    'Good Morning',
            'good_afternoon':  'Good Afternoon',
            'good_evening':    'Good Evening',
            'how_are_you':     'How are you?',
            'i_am_fine':       'I am fine',
            'i_am_not_fine':   'I am not fine',
            'whats_your_name': 'What is your name?',
            'my_name_is':      'My name is...',
            'sorry':           'Sorry',
            'thank_you':       'Thank you',
        }

        # Load MLP model
        self.model = None
        self.scaler = None
        if os.path.exists(self.model_path):
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
                if isinstance(model_data, dict):
                    self.model = model_data.get('model')
                    self.scaler = model_data.get('scaler')
                else:
                    self.model = model_data
            print(f"[Detector] MLP model loaded from {self.model_path}")
        else:
            print(f"[Detector] WARNING: Model file not found at {self.model_path}")

        # Load LSTM model
        self.lstm_model = None
        self.lstm_labels = None
        self._load_lstm()

        # LSTM state
        self.lstm_buffer = []
        self.LSTM_SEQ_LEN = 80
        self.LSTM_CONF_THRESHOLD = 0.85
        self.lstm_cooldown = 0
        self.LSTM_COOLDOWN_FRAMES = 30
        self.no_hand_frames = 0
        self.NO_HAND_RESET = 15   # more tolerant: 15 frames before buffer reset
        self.phrase_display_until = 0
        self._prev_lstm_frame = None  # for velocity features

        # Alphabet: minimum frames a sign must be held before committing
        self.MLP_CONF_THRESHOLD = 0.75
        self.MLP_HOLD_FRAMES = 8     # must hold same letter for 8 frames
        self.last_committed_sign = None
        self.last_committed_time = 0
        self.SIGN_COOLDOWN_SEC = 1.2  # seconds before same sign can fire again

        # MediaPipe — only called inside _detection_loop
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            model_complexity=0,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6,
            max_num_hands=2
        )

        # Camera
        self.camera = cv2.VideoCapture(camera_index)
        self.ret = False
        self.frame = None
        self.annotated = None
        self._running = True
        self._lock = threading.Lock()
        self._processing_lock = threading.Lock()

        # Detection state
        self.detection_history = []
        self.MAX_HISTORY = 20
        self.latest_detection = {"sign": None, "conf": 0.0, "timestamp": None}
        self.detection_buffer = []
        self.BUFFER_SIZE = 5        # require 5 consistent frames before committing

        # 'alphabet' = MLP only | 'phrase' = LSTM only
        self.detection_mode = 'alphabet'

        if not self.camera.isOpened():
            print(f"[Detector] ERROR: Could not open camera {camera_index}")
        else:
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
            self.camera.set(cv2.CAP_PROP_FPS, 20)
            print(f"[Detector] Camera opened (index {camera_index})")

        threading.Thread(target=self._detection_loop, daemon=True).start()
        self._warmup_camera()

    # ------------------------------------------------------------------
    # Public: mode switching
    # ------------------------------------------------------------------

    def set_mode(self, mode):
        """Switch between 'alphabet' (MLP only) and 'phrase' (LSTM only)."""
        if mode not in ('alphabet', 'phrase'):
            return
        self.detection_mode = mode
        self.lstm_buffer = []
        self.lstm_cooldown = 0
        self.detection_buffer = []
        self.no_hand_frames = 0
        self.last_committed_sign = None
        self.last_committed_time = 0
        with self._lock:
            self.latest_detection.update({"sign": None, "conf": 0.0, "timestamp": None})
        print(f"[Detector] Mode switched to: {mode}")

    # ------------------------------------------------------------------
    # Background thread
    # ------------------------------------------------------------------

    def _warmup_camera(self):
        def warmup():
            print("[Detector] Warming up camera...")
            for _ in range(100):
                if self.ret and self.frame is not None:
                    print("[Detector] Camera ready.")
                    return
                time.sleep(0.05)
            print("[Detector] WARNING: Camera warmup timeout.")
        threading.Thread(target=warmup, daemon=True).start()

    def _detection_loop(self):
        if not self.camera.isOpened():
            print("[Detector] Camera not open, exiting detection loop.")
            return

        consecutive_failures = 0
        while self._running:
            success, frame = self.camera.read()
            if not success:
                consecutive_failures += 1
                self.ret = False
                time.sleep(0.01)
                if consecutive_failures > 50:
                    self._recover_camera()
                    consecutive_failures = 0
                continue

            consecutive_failures = 0
            self.ret = True
            self.frame = frame

            image = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            with self._processing_lock:
                results = self.hands.process(rgb)
                self._run_detection(results, image)
                self._draw_overlay(image)
            self.annotated = image
            time.sleep(0.01)  # ~30fps cap, frees CPU for other threads

    def process_external_frame(self, frame):
        """Process a frame uploaded by a browser camera."""
        image = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        with self._processing_lock:
            results = self.hands.process(rgb)
            self._run_detection(results, image)
            self._draw_overlay(image)
        with self._lock:
            self.annotated = image
        return image

    def _recover_camera(self):
        print("[Detector] Attempting camera recovery...")
        try:
            self.camera.release()
            time.sleep(0.5)
            self.camera = cv2.VideoCapture(0)
            time.sleep(0.5)
            if self.camera.isOpened():
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
                self.camera.set(cv2.CAP_PROP_FPS, 20)
                print("[Detector] Camera recovered.")
        except Exception as e:
            print(f"[Detector] Recovery error: {e}")

    # ------------------------------------------------------------------
    # Detection logic
    # ------------------------------------------------------------------

    def _run_detection(self, results, image):
        if results and results.multi_hand_landmarks:
            for hand_lm in results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(image, hand_lm, self.mp_hands.HAND_CONNECTIONS)
            self.no_hand_frames = 0

            if self.detection_mode == 'phrase':
                self._run_lstm(results, image)
            else:
                self._run_mlp(results)
        else:
            self.no_hand_frames += 1
            if self.no_hand_frames >= self.NO_HAND_RESET:
                self.lstm_buffer = []
                self._prev_lstm_frame = None
            self.detection_buffer = []
            self.last_committed_sign = None  # reset so next sign fires immediately
            with self._lock:
                current = self.latest_detection.get("sign")
                if current and current not in self.PHRASE_DISPLAY:
                    self.latest_detection.update({"sign": None, "conf": 0.0, "timestamp": None})
                elif current and current in self.PHRASE_DISPLAY:
                    if self.phrase_display_until > 0 and time.time() > self.phrase_display_until:
                        self.phrase_display_until = 0
                        self.latest_detection.update({"sign": None, "conf": 0.0, "timestamp": None})

    def _run_lstm(self, results, image):
        if self.lstm_cooldown > 0:
            self.lstm_cooldown -= 1
            cv2.putText(image, f"Cooldown... {self.lstm_cooldown}",
                        (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)
            return

        self.lstm_buffer.append(self._extract_two_hand_landmarks(results))
        cv2.putText(image, f"Recording... {len(self.lstm_buffer)}/{self.LSTM_SEQ_LEN}",
                    (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        if len(self.lstm_buffer) == self.LSTM_SEQ_LEN:
            phrase, conf = self._predict_lstm()
            print(f"[LSTM] {phrase} ({conf*100:.1f}%)")
            self.lstm_buffer = []
            self._prev_lstm_frame = None  # reset velocity so next sequence starts clean
            self.lstm_cooldown = self.LSTM_COOLDOWN_FRAMES
            if phrase and conf >= self.LSTM_CONF_THRESHOLD:
                self._commit_phrase(phrase, conf)

    def _run_mlp(self, results):
        if self.model is None:
            return
        hand_landmarks = results.multi_hand_landmarks[0]
        landmarks = []
        for lm in hand_landmarks.landmark:
            landmarks.extend([lm.x, lm.y, lm.z])
        if len(landmarks) < 63:
            return
        try:
            arr = self._normalize_landmarks(landmarks).reshape(1, -1)
            if self.scaler is not None:
                arr = self.scaler.transform(arr)
            pred = self.model.predict(arr)
            probs = self.model.predict_proba(arr)
            conf = float(np.max(probs))
            sign = self.SIGN_NAMES[int(pred[0])]

            if conf >= self.MLP_CONF_THRESHOLD:
                self.detection_buffer.append(sign)
                if len(self.detection_buffer) > self.BUFFER_SIZE:
                    self.detection_buffer.pop(0)

                # Must have BUFFER_SIZE consistent frames of the same sign
                if (len(self.detection_buffer) >= self.BUFFER_SIZE
                        and len(set(self.detection_buffer)) == 1):
                    now = time.time()
                    # Cooldown: same sign cannot fire again within SIGN_COOLDOWN_SEC
                    if (sign != self.last_committed_sign
                            or now - self.last_committed_time >= self.SIGN_COOLDOWN_SEC):
                        self.last_committed_sign = sign
                        self.last_committed_time = now
                        with self._lock:
                            if not self.detection_history or self.detection_history[-1]["sign"] != sign:
                                self.detection_history.append({"sign": sign, "conf": conf, "ts": now})
                                if len(self.detection_history) > self.MAX_HISTORY:
                                    self.detection_history.pop(0)
                            self.latest_detection.update({"sign": sign, "conf": conf, "timestamp": now})
                        print(f"[MLP] {sign} ({conf*100:.1f}%)")
            else:
                self.detection_buffer = []
                with self._lock:
                    current = self.latest_detection.get("sign")
                    if current and current not in self.PHRASE_DISPLAY:
                        self.latest_detection.update({"sign": None, "conf": 0.0, "timestamp": None})
        except Exception as e:
            print(f"[Detector] MLP error: {e}")

    def _commit_phrase(self, phrase, conf):
        ts = time.time()
        self.phrase_display_until = ts + 4.0
        with self._lock:
            if not self.detection_history or self.detection_history[-1]["sign"] != phrase:
                self.detection_history.append({"sign": phrase, "conf": conf, "ts": ts})
                if len(self.detection_history) > self.MAX_HISTORY:
                    self.detection_history.pop(0)
            self.latest_detection.update({"sign": phrase, "conf": conf, "timestamp": ts})
        print(f"[Detector] Phrase: {phrase} ({conf*100:.1f}%)")

    def _draw_overlay(self, image):
        # Show current mode on frame
        mode_label = "ALPHABET" if self.detection_mode == 'alphabet' else "PHRASE"
        mode_color = (255, 165, 0) if self.detection_mode == 'alphabet' else (0, 200, 100)
        cv2.putText(image, f"Mode: {mode_label}", (10, image.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)
        cv2.putText(image, f"Mode: {mode_label}", (10, image.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, mode_color, 1)

        with self._lock:
            sign = self.latest_detection.get("sign")
            conf = self.latest_detection.get("conf", 0.0)
        if sign:
            display = self.PHRASE_DISPLAY.get(sign, sign.upper())
            text = f'{display} ({int(conf*100)}%)'
            cv2.putText(image, text, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 3)
            cv2.putText(image, text, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 1)
            if sign in self.FILIPINO_TRANSLATIONS:
                fil = self.FILIPINO_TRANSLATIONS[sign]
                cv2.putText(image, fil, (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
                cv2.putText(image, fil, (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 1)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _normalize_landmarks(self, landmarks):
        """Wrist-relative, scale-normalized — must match train_model.py."""
        pts = np.array(landmarks).reshape(21, 3)
        pts = pts - pts[0]
        scale = np.max(np.abs(pts))
        if scale > 0:
            pts = pts / scale
        return pts.flatten()

    def _normalize_hand(self, flat63):
        """Wrist-relative + scale-normalized for a single hand (63 values)."""
        pts = flat63.reshape(21, 3)
        pts = pts - pts[0]  # wrist origin
        scale = np.max(np.abs(pts))
        if scale > 0:
            pts = pts / scale
        return pts.flatten()

    def _extract_two_hand_landmarks(self, results):
        """Returns 252-dim vector: 126 normalized landmarks + 126 velocity (delta)."""
        hand_data = [np.zeros(63), np.zeros(63)]
        if results.multi_hand_landmarks:
            for i, hand_lm in enumerate(results.multi_hand_landmarks[:2]):
                raw = np.array([[lm.x, lm.y, lm.z] for lm in hand_lm.landmark]).flatten()
                hand_data[i] = self._normalize_hand(raw)
        landmarks = np.concatenate(hand_data)  # (126,)

        if self._prev_lstm_frame is not None:
            velocity = landmarks - self._prev_lstm_frame  # (126,)
        else:
            velocity = np.zeros(126)
        self._prev_lstm_frame = landmarks.copy()
        return np.concatenate([landmarks, velocity])  # (252,)

    def _predict_lstm(self):
        try:
            seq = np.array(self.lstm_buffer, dtype=np.float32)
            tensor = torch.tensor(seq).unsqueeze(0)
            with torch.no_grad():
                logits = self.lstm_model(tensor)
                probs = torch.softmax(logits, dim=1)
                conf, idx = probs.max(dim=1)
                label = self.lstm_labels.inverse_transform([int(idx.item())])[0]
                return label, float(conf.item())
        except Exception as e:
            print(f"[Detector] LSTM predict error: {e}")
            return None, 0.0

    def _load_lstm(self):
        try:
            if os.path.exists('lstm_model.pt') and os.path.exists('lstm_labels.pkl'):
                with open('lstm_labels.pkl', 'rb') as f:
                    self.lstm_labels = pickle.load(f)
                num_classes = len(self.lstm_labels.classes_)

                class LSTMClassifier(nn.Module):
                    def __init__(self):
                        super().__init__()
                        self.lstm = nn.LSTM(252, 64, 1, batch_first=True)
                        self.dropout = nn.Dropout(0.5)
                        self.fc = nn.Linear(64, num_classes)
                    def forward(self, x):
                        _, (h, _) = self.lstm(x)
                        return self.fc(self.dropout(h[-1]))

                checkpoint = torch.load('lstm_model.pt', map_location='cpu')
                model = LSTMClassifier()
                model.load_state_dict(checkpoint['model_state'])
                model.eval()
                self.lstm_model = model
                print(f"[Detector] LSTM loaded. Classes: {list(self.lstm_labels.classes_)}")
            else:
                print("[Detector] No LSTM model found.")
        except Exception as e:
            print(f"[Detector] LSTM load error: {e}")

    def reload_model(self):
        if os.path.exists(self.model_path):
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)

    def get_latest(self):
        with self._lock:
            detection = dict(self.latest_detection)
        sign = detection["sign"]
        if sign:
            detection["display"] = self.PHRASE_DISPLAY.get(sign, sign.upper())
            detection["filipino"] = self.FILIPINO_TRANSLATIONS.get(sign, None)
        else:
            detection["display"] = None
            detection["filipino"] = None
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

    def _process_frame(self, frame=None):
        if self.annotated is not None:
            return self.annotated.copy()
        if frame is not None:
            return cv2.flip(frame, 1)
        return None

    def generate_frames(self):
        print("[Detector] generate_frames() started")
        target_fps = 20
        interval = 1.0 / target_fps
        last_sent = 0
        while self._running:
            now = time.time()
            if self.annotated is None or (now - last_sent) < interval:
                time.sleep(0.01)
                continue
            image = self.annotated.copy()
            ret, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 60])
            if not ret:
                continue
            last_sent = time.time()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

    def run_window(self):
        cv2.namedWindow('Sign Language Detector')
        while True:
            if self.annotated is not None:
                cv2.imshow('Sign Language Detector', self.annotated)
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
