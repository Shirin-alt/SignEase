import numpy as np
import torch
import torch.nn as nn
import pickle
import os
from sklearn.metrics import classification_report, confusion_matrix

DATA_PATH = os.path.join('data', 'sequences')
SEQUENCE_LENGTH = 30
INPUT_SIZE = 126

SIGNS = [
    'hi', 'good_morning', 'good_afternoon', 'good_evening',
    'how_are_you', 'i_am_fine', 'i_am_not_fine',
    'whats_your_name', 'my_name_is', 'sorry', 'thank_you'
]

with open('lstm_labels.pkl', 'rb') as f:
    le = pickle.load(f)

num_classes = len(le.classes_)

class LSTMClassifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(INPUT_SIZE, 128, 2, batch_first=True, dropout=0.3)
        self.dropout = nn.Dropout(0.3)
        self.fc = nn.Linear(128, num_classes)
    def forward(self, x):
        _, (h, _) = self.lstm(x)
        return self.fc(self.dropout(h[-1]))

checkpoint = torch.load('lstm_model.pt', map_location='cpu')
model = LSTMClassifier()
model.load_state_dict(checkpoint['model_state'])
model.eval()

X, y_true = [], []
for sign in SIGNS:
    path = os.path.join(DATA_PATH, sign)
    if not os.path.exists(path):
        continue
    for f in os.listdir(path):
        if f.endswith('.npy'):
            seq = np.load(os.path.join(path, f))
            if seq.shape == (SEQUENCE_LENGTH, INPUT_SIZE):
                X.append(seq)
                y_true.append(sign)

print(f"Total samples: {len(X)}\n")

y_pred = []
for seq in X:
    tensor = torch.tensor(seq, dtype=torch.float32).unsqueeze(0)
    with torch.no_grad():
        logits = model(tensor)
        probs = torch.softmax(logits, dim=1)
        idx = probs.argmax(dim=1).item()
        y_pred.append(le.inverse_transform([idx])[0])

print("=== Classification Report ===")
print(classification_report(y_true, y_pred, target_names=sorted(set(y_true))))

print("\n=== Confusion Matrix ===")
labels = sorted(set(y_true))
cm = confusion_matrix(y_true, y_pred, labels=labels)
header = f"{'':20}" + "".join(f"{l[:8]:>10}" for l in labels)
print(header)
for i, row in enumerate(cm):
    print(f"{labels[i]:20}" + "".join(f"{v:>10}" for v in row))
