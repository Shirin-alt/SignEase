"""Interactive data collector for alphabet + original project labels.

Usage:
  python collect_alphabet.py [-n SAMPLES]

Controls (while running):
  - Press a..z to start collecting samples for that letter.
  - Press 1..5 to collect for original labels: 1=hello,2=thanks,3=yes,4=no,5=iloveyou
  - Press 'q' to cancel current collection early.
  - Press ESC to exit the program.

Saves: `data/<label>/<index>.npy` (flat landmark vectors saved with numpy)
"""

import argparse
import time
from pathlib import Path
import cv2
import mediapipe as mp
import numpy as np
import os


ORIGINAL_LABELS = ["hello", "thanks", "yes", "no", "iloveyou"]
# Alphabet without 'q' since no data collected for it
ALPHABET = [chr(i) for i in range(ord('a'), ord('z') + 1) if chr(i) != 'q']
SIGN_NAMES = ORIGINAL_LABELS + ALPHABET


def ensure_dirs(base='data'):
    basep = Path(base)
    for label in SIGN_NAMES:
        (basep / label).mkdir(parents=True, exist_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--samples', type=int, default=500,
                        help='Number of samples to collect per label (default: 500)')
    parser.add_argument('--camera', type=int, default=0, help='Camera index (default 0)')
    args = parser.parse_args()

    NUM_SAMPLES = args.samples
    DATA_PATH = Path('data')

    ensure_dirs(DATA_PATH)

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)
    mp_drawing = mp.solutions.drawing_utils

    cap = cv2.VideoCapture(args.camera)

    print('Interactive collector started')
    print('Press a..z to collect letters. Press 1..5 for original labels:')
    for i, lab in enumerate(ORIGINAL_LABELS, start=1):
        print(f'  {i}: {lab}')
    print("Press 'q' to cancel current collection, ESC to exit.")

    current_label = None
    counter = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print('Camera read failed')
                break

            display = frame.copy()
            h, w = display.shape[:2]

            if current_label:
                cv2.putText(display, f"Collecting '{current_label}': {counter}/{NUM_SAMPLES}", (10, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2, cv2.LINE_AA)
            else:
                cv2.putText(display, "Press letter (a-z) or 1-5 to collect", (10, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (50, 50, 50), 2, cv2.LINE_AA)

            cv2.imshow('Collector', display)
            key = cv2.waitKey(1) & 0xFF

            # ESC to exit
            if key == 27:
                print('Exiting')
                break

            # Cancel current collection
            if key == ord('q'):
                if current_label:
                    print(f'Cancelled collection for {current_label}')
                current_label = None
                counter = 0
                continue

            # If not currently collecting, check for start keys
            if not current_label:
                # digits 1..5 map to original labels
                if ord('1') <= key <= ord('5'):
                    idx = key - ord('1')
                    if idx < len(ORIGINAL_LABELS):
                        current_label = ORIGINAL_LABELS[idx]
                        # start index at existing file count
                        counter = len(list((DATA_PATH / current_label).glob('*.npy')))
                        print(f"Starting collection for {current_label}. Existing: {counter}")
                        time.sleep(0.3)
                        continue

                # letters a..z
                if ord('a') <= key <= ord('z'):
                    current_label = chr(key)
                    counter = len(list((DATA_PATH / current_label).glob('*.npy')))
                    print(f"Starting collection for {current_label}. Existing: {counter}")
                    time.sleep(0.3)
                    continue

            # If collecting, capture landmarks when a hand is detected
            if current_label:
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = hands.process(image)
                if results.multi_hand_landmarks:
                    # use first detected hand
                    hand_landmarks = results.multi_hand_landmarks[0]
                    landmarks = []
                    for lm in hand_landmarks.landmark:
                        landmarks.extend([lm.x, lm.y, lm.z])

                    # save sample
                    out_path = DATA_PATH / current_label / f"{counter}.npy"
                    np.save(out_path, np.array(landmarks))
                    counter += 1
                    print(f"Saved {out_path}")

                    if counter >= NUM_SAMPLES:
                        print(f"Finished collecting {current_label} ({NUM_SAMPLES} samples)")
                        current_label = None
                        counter = 0

    finally:
        cap.release()
        cv2.destroyAllWindows()
        hands.close()


if __name__ == '__main__':
    main()
