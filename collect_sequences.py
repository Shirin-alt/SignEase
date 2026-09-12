import cv2
import mediapipe as mp
import numpy as np
import os

# --- CONFIG ---
SEQUENCE_LENGTH = 80        # frames per sequence
SEQUENCES_PER_SIGN = 500    # sequences to collect per phrase
DATA_PATH = os.path.join('data', 'sequences')

# FSL Phrases (motion-based, 2-hand)
SIGNS = [
    'hi',
    'good_morning',
    'good_afternoon',
    'good_evening',
    'how_are_you',
    'i_am_fine',
    'i_am_not_fine',
    'whats_your_name',
    'my_name_is',
    'sorry',
    'thank_you',
]

SIGN_DISPLAY = {
    'hi':               'Hi',
    'good_morning':     'Good Morning',
    'good_afternoon':   'Good Afternoon',
    'good_evening':     'Good Evening',
    'how_are_you':      'How are you?',
    'i_am_fine':        'I am fine',
    'i_am_not_fine':    'I am not fine',
    'whats_your_name':  'What is your name?',
    'my_name_is':       'My name is...',
    'sorry':            'Sorry',
    'thank_you':        'Thank you',
}

# Each frame = 126 normalized landmarks + 126 velocity = 252 values
LANDMARK_SIZE = 252

# Setup folders
for sign in SIGNS:
    os.makedirs(os.path.join(DATA_PATH, sign), exist_ok=True)

# MediaPipe - 2 hands enabled
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    static_image_mode=False,
    model_complexity=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7,
    max_num_hands=2   # <-- 2 hands
)

def normalize_hand(flat63):
    """Wrist-relative + scale-normalized for one hand."""
    pts = flat63.reshape(21, 3)
    pts = pts - pts[0]
    scale = np.max(np.abs(pts))
    if scale > 0:
        pts = pts / scale
    return pts.flatten()

_prev_frame = None  # module-level state for velocity

def reset_velocity():
    global _prev_frame
    _prev_frame = None

def extract_landmarks(results):
    """Returns 252-dim: 126 normalized landmarks + 126 velocity (delta from prev frame)."""
    global _prev_frame
    hand_data = [np.zeros(63), np.zeros(63)]
    if results.multi_hand_landmarks:
        for i, hand_lm in enumerate(results.multi_hand_landmarks[:2]):
            raw = np.array([[lm.x, lm.y, lm.z] for lm in hand_lm.landmark]).flatten()
            hand_data[i] = normalize_hand(raw)
    landmarks = np.concatenate(hand_data)  # (126,)
    velocity = (landmarks - _prev_frame) if _prev_frame is not None else np.zeros(126)
    _prev_frame = landmarks.copy()
    return np.concatenate([landmarks, velocity])  # (252,)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print("=== FSL Sequence Collector ===")
print(f"Phrases: {len(SIGNS)}")
print(f"Sequences per phrase: {SEQUENCES_PER_SIGN}")
print(f"Frames per sequence: {SEQUENCE_LENGTH}")
print(f"Landmark size per frame: {LANDMARK_SIZE} (2 hands x 63)")
print("\nControls:")
print("  SPACE = start recording")
print("  S     = skip to next phrase")
print("  Q     = quit\n")

for sign in SIGNS:
    display_name = SIGN_DISPLAY[sign]

    # Count existing to allow resuming
    existing = len([f for f in os.listdir(os.path.join(DATA_PATH, sign)) if f.endswith('.npy')])
    print(f"\n--- '{display_name}' ({existing}/{SEQUENCES_PER_SIGN} already collected) ---")

    if existing >= SEQUENCES_PER_SIGN:
        print(f"  Already complete, skipping.")
        continue

    seq_num = existing
    while seq_num < SEQUENCES_PER_SIGN:

        # --- Wait for SPACE ---
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)

            if results.multi_hand_landmarks:
                for hand_lm in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(frame, hand_lm, mp_hands.HAND_CONNECTIONS)

            # Hand count indicator
            hand_count = len(results.multi_hand_landmarks) if results.multi_hand_landmarks else 0
            hand_color = (0, 255, 0) if hand_count >= 1 else (0, 0, 255)
            cv2.putText(frame, f"Hands: {hand_count}", (480, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, hand_color, 2)

            cv2.putText(frame, f"Sign: {display_name}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
            cv2.putText(frame, f"Seq: {seq_num}/{SEQUENCES_PER_SIGN}", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
            cv2.putText(frame, "SPACE=record  S=skip phrase  Q=quit", (10, 460),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)
            cv2.imshow('FSL Collector', frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord(' '):
                break
            if key == ord('s'):
                seq_num = SEQUENCES_PER_SIGN  # skip this sign
                break
            if key == ord('q'):
                cap.release()
                cv2.destroyAllWindows()
                hands.close()
                print("Quit.")
                exit()

        if seq_num >= SEQUENCES_PER_SIGN:
            break

        # --- Countdown 3-2-1 ---
        reset_velocity()  # reset velocity between sequences
        for countdown in range(3, 0, -1):
            ret, frame = cap.read()
            frame = cv2.flip(frame, 1)
            cv2.putText(frame, str(countdown), (290, 270),
                        cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 0, 255), 10)
            cv2.putText(frame, display_name, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
            cv2.imshow('FSL Collector', frame)
            cv2.waitKey(700)

        # --- Record SEQUENCE_LENGTH frames ---
        sequence = []
        for frame_num in range(SEQUENCE_LENGTH):
            ret, frame = cap.read()
            if not ret:
                sequence.append(np.zeros(LANDMARK_SIZE))
                continue

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)

            landmarks = extract_landmarks(results)
            sequence.append(landmarks)

            if results.multi_hand_landmarks:
                for hand_lm in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(frame, hand_lm, mp_hands.HAND_CONNECTIONS)

            # Progress bar
            progress = int((frame_num / SEQUENCE_LENGTH) * 400)
            cv2.rectangle(frame, (10, 440), (410, 460), (50, 50, 50), -1)
            cv2.rectangle(frame, (10, 440), (10 + progress, 460), (0, 255, 0), -1)
            cv2.putText(frame, f"Recording {display_name}... {frame_num+1}/{SEQUENCE_LENGTH}", (10, 430),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)

            hand_count = len(results.multi_hand_landmarks) if results.multi_hand_landmarks else 0
            hand_color = (0, 255, 0) if hand_count >= 1 else (0, 0, 255)
            cv2.putText(frame, f"Hands: {hand_count}", (480, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, hand_color, 2)

            cv2.imshow('FSL Collector', frame)
            cv2.waitKey(1)

        # --- Save ---
        save_path = os.path.join(DATA_PATH, sign, f"{seq_num}.npy")
        np.save(save_path, np.array(sequence))  # shape: (30, 126)
        print(f"  Saved seq {seq_num}: {save_path}  shape={np.array(sequence).shape}")
        seq_num += 1

    print(f"  Done: '{display_name}'")

cap.release()
cv2.destroyAllWindows()
hands.close()
print("\nAll sequences collected!")
print("Next step: run train_lstm.py")
