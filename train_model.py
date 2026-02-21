import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report
import pickle
import os

# --- Configuration ---
DATA_PATH = 'data'
# Keep original labels and append alphabet a-z. Order must match folders in `data/`.
SIGN_NAMES = [
    "hello", "thanks", "yes", "no", "iloveyou",
    'a','b','c','d','e','f','g','h','i','j','k','l','m',
    'n','o','p','r','s','t','u','v','w','x','y','z'
]
MODEL_PATH = 'sign_classifier.p' # The file to save our trained model

# --- Load and Prepare Data ---
labels = []
data = []

print("Loading data...")
# Loop through each sign folder
for sign_idx, sign_name in enumerate(SIGN_NAMES):
    sign_path = os.path.join(DATA_PATH, sign_name)
    # Loop through each .npy file in the folder
    for npy_file in os.listdir(sign_path):
        if npy_file.endswith('.npy'):
            # Load the landmark data
            landmarks = np.load(os.path.join(sign_path, npy_file))
            data.append(landmarks)
            labels.append(sign_idx)

# Convert lists to numpy arrays
data = np.array(data)
labels = np.array(labels)

print(f"Data shape: {data.shape}")
print(f"Labels shape: {labels.shape}")

# --- Train the Model ---
# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(data, labels, test_size=0.2, random_state=42, stratify=labels)

# Normalize features for neural network
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Initialize and train MLPClassifier (neural network) — better for many classes
print("Training neural network model...")
model = MLPClassifier(
    hidden_layer_sizes=(256, 128, 64),  # 3 hidden layers
    max_iter=500,
    early_stopping=True,
    validation_fraction=0.2,
    random_state=42,
    verbose=1
)
model.fit(X_train_scaled, y_train)

# --- Evaluate the Model ---
y_pred = model.predict(X_test_scaled)
accuracy = accuracy_score(y_test, y_pred)
print(f"\nModel Accuracy: {accuracy * 100:.2f}%")

# Only report on classes that exist in test set
unique_labels = np.unique(y_test)
report_names = [SIGN_NAMES[i] for i in unique_labels]
print("\nClassification Report:")
print(classification_report(y_test, y_pred, labels=unique_labels, target_names=report_names))

# --- Save the Model and Scaler ---
# We need to save both the model and the scaler so predictions use same normalization
model_data = {'model': model, 'scaler': scaler}
with open(MODEL_PATH, 'wb') as f:
    pickle.dump(model_data, f)

print(f"Model and scaler saved to {MODEL_PATH}")