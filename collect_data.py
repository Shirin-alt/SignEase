import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
import os

# --- Configuration ---
# Change these to the signs you want to collect. We keep the original
# labels and append the alphabet a-z so data can include both sets.
SIGN_NAMES = [
    "hello", "thanks", "yes", "no", "iloveyou",
    'a','b','c','d','e','f','g','h','i','j','k','l','m',
    'n','o','p','r','s','t','u','v','w','x','y','z'
]
NUM_SAMPLES_PER_SIGN = 500 # Increased to 500 per user request

# --- Setup MediaPipe ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

# --- Setup Data Storage ---
DATA_PATH = 'data'
if not os.path.exists(DATA_PATH):
    os.makedirs(DATA_PATH)

# --- Main Loop ---
cap = cv2.VideoCapture(0)

for sign_idx, sign_name in enumerate(SIGN_NAMES):
    # Create a folder for each sign
    sign_path = os.path.join(DATA_PATH, sign_name)
    if not os.path.exists(sign_path):
        os.makedirs(sign_path)
        
    print(f"--- Collecting data for '{sign_name}' ---")
    print("Press 'c' to start collecting, 'q' to quit.")

    # Wait for user to be ready
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        cv2.putText(frame, f"Ready to collect: '{sign_name}'", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.imshow('Data Collection', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('c'):
            break
        if key == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            exit()

    # Collect the samples
    counter = 0
    while counter < NUM_SAMPLES_PER_SIGN:
        ret, frame = cap.read()
        if not ret:
            break

        # Flip the image horizontally for a later selfie-view display
        # and convert the BGR image to RGB.
        image = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
        
        # Process the image and find hands
        results = hands.process(image)

        # Convert the image color back so it can be displayed
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                
                # Extract landmark coordinates
                landmarks = []
                for lm in hand_landmarks.landmark:
                    landmarks.extend([lm.x, lm.y, lm.z]) # x, y, z coordinates
                
                # Save the landmarks to a file
                np.save(os.path.join(sign_path, f"{counter}.npy"), np.array(landmarks))
                counter += 1
                
                cv2.putText(image, f"Collecting {counter}/{NUM_SAMPLES_PER_SIGN}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

        cv2.imshow('Data Collection', image)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
print("--- Data collection complete! ---")