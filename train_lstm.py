import os
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import pickle

# --- CONFIG ---
DATA_PATH = os.path.join('data', 'sequences')
MODEL_PATH = 'lstm_model.pt'
LABEL_PATH = 'lstm_labels.pkl'

SEQUENCE_LENGTH = 80
INPUT_SIZE = 252
HIDDEN_SIZE = 64       # small model for small dataset
NUM_LAYERS = 1         # single layer — less capacity = less overfitting
DROPOUT = 0.5
BATCH_SIZE = 16        # smaller batch = more gradient noise = better generalization
EPOCHS = 200
LEARNING_RATE = 0.0005 # slower learning
WEIGHT_DECAY = 1e-3

SIGNS = [
    'hi', 'good_morning', 'good_afternoon', 'good_evening',
    'how_are_you', 'i_am_fine', 'i_am_not_fine',
    'whats_your_name', 'my_name_is', 'sorry', 'thank_you'
]

# --- Augmentation ---
def augment_sequence(seq):
    aug = seq.copy()
    aug[:, :126] += np.random.normal(0, 0.008, (SEQUENCE_LENGTH, 126))
    aug[:, :126] *= np.random.uniform(0.92, 1.08)
    # random frame dropout: blank out 1-3 random frames
    n_drop = np.random.randint(1, 4)
    drop_idx = np.random.choice(SEQUENCE_LENGTH, n_drop, replace=False)
    aug[drop_idx] = 0.0
    return aug.astype(np.float32)


# --- Dataset with online augmentation ---
class SequenceDataset(Dataset):
    def __init__(self, X, y, augment=False):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.long)
        self.augment = augment

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        x = self.X[idx].numpy()
        if self.augment:
            x = augment_sequence(x)
        return torch.tensor(x, dtype=torch.float32), self.y[idx]

# --- LSTM Model ---
class LSTMClassifier(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, num_classes, dropout):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers,
                            batch_first=True, dropout=dropout if num_layers > 1 else 0)
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_size, num_classes)

    def forward(self, x):
        _, (hidden, _) = self.lstm(x)
        out = self.dropout(hidden[-1])
        return self.fc(out)

# --- Load Data ---
print("Loading sequences...")
X, y_labels = [], []

for sign in SIGNS:
    sign_path = os.path.join(DATA_PATH, sign)
    if not os.path.exists(sign_path):
        print(f"  WARNING: {sign_path} not found, skipping.")
        continue
    files = [f for f in os.listdir(sign_path) if f.endswith('.npy')]
    for f in files:
        seq = np.load(os.path.join(sign_path, f))
        if seq.shape == (SEQUENCE_LENGTH, INPUT_SIZE):
            X.append(seq)
            y_labels.append(sign)

X = np.array(X, dtype=np.float32)
print(f"Total sequences loaded: {len(X)}")

# Encode labels
le = LabelEncoder()
y = le.fit_transform(y_labels)
NUM_CLASSES = len(le.classes_)
print(f"Classes ({NUM_CLASSES}): {list(le.classes_)}")

# Save label encoder
with open(LABEL_PATH, 'wb') as f:
    pickle.dump(le, f)
print(f"Label encoder saved to {LABEL_PATH}")

# --- Train/Val Split ---
X_train, X_val, y_train, y_val = train_test_split(
    X, y, test_size=0.15, random_state=42, stratify=y
)
print(f"Train: {len(X_train)}  Val: {len(X_val)}")

# augment=True means each sample is randomly augmented on-the-fly every epoch
train_loader = DataLoader(SequenceDataset(X_train, y_train, augment=True), batch_size=BATCH_SIZE, shuffle=True)
val_loader   = DataLoader(SequenceDataset(X_val,   y_val,   augment=False), batch_size=BATCH_SIZE)

# --- Model, Loss, Optimizer ---
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

model = LSTMClassifier(INPUT_SIZE, HIDDEN_SIZE, NUM_LAYERS, NUM_CLASSES, DROPOUT).to(device)
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=15, factor=0.5, min_lr=1e-5)

# --- Training Loop ---
best_val_acc = 0.0
train_loss_history = []
val_loss_history = []
train_acc_history = []
val_acc_history = []
no_improve = 0
PATIENCE = 50

print("\nStarting training...")
for epoch in range(1, EPOCHS + 1):
    # Train
    model.train()
    train_loss, train_correct = 0.0, 0
    for xb, yb in train_loader:
        xb, yb = xb.to(device), yb.to(device)
        optimizer.zero_grad()
        out = model(xb)
        loss = criterion(out, yb)
        loss.backward()
        optimizer.step()
        train_loss += loss.item() * len(xb)
        train_correct += (out.argmax(1) == yb).sum().item()

    # Validate
    model.eval()
    val_loss, val_correct = 0.0, 0
    with torch.no_grad():
        for xb, yb in val_loader:
            xb, yb = xb.to(device), yb.to(device)
            out = model(xb)
            val_loss += criterion(out, yb).item() * len(xb)
            val_correct += (out.argmax(1) == yb).sum().item()

    train_acc = train_correct / len(X_train)
    val_acc   = val_correct   / len(X_val)
    avg_train_loss = train_loss / len(X_train)
    avg_val_loss   = val_loss   / len(X_val)

    train_loss_history.append(avg_train_loss)
    val_loss_history.append(avg_val_loss)
    train_acc_history.append(float(train_acc))
    val_acc_history.append(float(val_acc))

    scheduler.step(avg_val_loss)

    if epoch % 10 == 0 or epoch == 1:
        print(f"Epoch {epoch:3d}/{EPOCHS} | "
              f"Train Loss: {avg_train_loss:.4f} Acc: {train_acc:.4f} | "
              f"Val Loss: {avg_val_loss:.4f} Acc: {val_acc:.4f}")

    # Save best model + early stopping
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        no_improve = 0
        torch.save({
            'model_state': model.state_dict(),
            'input_size': INPUT_SIZE,
            'hidden_size': HIDDEN_SIZE,
            'num_layers': NUM_LAYERS,
            'num_classes': NUM_CLASSES,
            'dropout': DROPOUT,
            'sequence_length': SEQUENCE_LENGTH,
            'train_loss_history': train_loss_history[:],
            'val_loss_history': val_loss_history[:],
            'train_acc_history': train_acc_history[:],
            'val_acc_history': val_acc_history[:],
        }, MODEL_PATH)
    else:
        no_improve += 1
        if no_improve >= PATIENCE:
            print(f"Early stopping at epoch {epoch} (no improvement for {PATIENCE} epochs)")
            break

print(f"\nTraining complete! Best val accuracy: {best_val_acc:.4f}")
print(f"Model saved to {MODEL_PATH}")
