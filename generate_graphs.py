"""
generate_graphs.py
Run: python generate_graphs.py
Saves all graphs as PNG files in graphs/ folder.
"""

import os
import numpy as np
import pickle
import torch
import torch.nn as nn
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.model_selection import train_test_split
import seaborn as sns

os.makedirs('graphs', exist_ok=True)

# ── Shared style ──────────────────────────────────────────────────────────────
BLUE   = '#0052cc'
CYAN   = '#00d4ff'
ORANGE = '#f7971e'
GREEN  = '#11998e'
RED    = '#e74c3c'
GRAY   = '#6c757d'
BG     = '#f8f9fa'

plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'axes.facecolor': BG,
    'figure.facecolor': 'white',
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.grid': True,
    'grid.alpha': 0.4,
    'grid.linestyle': '--',
})

SIGN_NAMES = ['a','b','c','d','e','f','g','h','i','j','k','l','m',
              'n','o','p','r','s','t','u','v','w','x','y','z']

PHRASE_NAMES = ['good_afternoon','good_evening','good_morning','hi',
                'how_are_you','i_am_fine','i_am_not_fine','my_name_is',
                'sorry','thank_you','whats_your_name']

PHRASE_DISPLAY = {
    'good_afternoon': 'Good Afternoon', 'good_evening': 'Good Evening',
    'good_morning': 'Good Morning',     'hi': 'Hi',
    'how_are_you': 'How are you?',      'i_am_fine': 'I am fine',
    'i_am_not_fine': 'I am not fine',   'my_name_is': 'My name is...',
    'sorry': 'Sorry',                   'thank_you': 'Thank you',
    'whats_your_name': "What's your name?",
}

# ── Load models ───────────────────────────────────────────────────────────────
print("Loading models...")
with open('sign_classifier.p', 'rb') as f:
    mlp_data = pickle.load(f)
mlp_model  = mlp_data['model']
mlp_scaler = mlp_data['scaler']

lstm_ckpt = torch.load('lstm_model.pt', map_location='cpu')

with open('lstm_labels.pkl', 'rb') as f:
    lstm_labels = pickle.load(f)

# ── Load datasets ─────────────────────────────────────────────────────────────
print("Loading alphabet data...")

def normalize_landmarks(landmarks):
    pts = landmarks.reshape(21, 3)
    pts = pts - pts[0]
    scale = np.max(np.abs(pts))
    if scale > 0:
        pts = pts / scale
    return pts.flatten()

X_alpha, y_alpha = [], []
for idx, sign in enumerate(SIGN_NAMES):
    path = os.path.join('data', sign)
    for f in os.listdir(path):
        if f.endswith('.npy'):
            lm = np.load(os.path.join(path, f))
            X_alpha.append(normalize_landmarks(lm))
            y_alpha.append(idx)
X_alpha = np.array(X_alpha)
y_alpha = np.array(y_alpha)

print("Loading sequence data...")
X_seq, y_seq_labels = [], []
for sign in PHRASE_NAMES:
    path = os.path.join('data', 'sequences', sign)
    if not os.path.exists(path):
        continue
    for f in os.listdir(path):
        if f.endswith('.npy'):
            seq = np.load(os.path.join(path, f))
            if seq.shape == (30, 126):
                X_seq.append(seq)
                y_seq_labels.append(sign)
X_seq = np.array(X_seq, dtype=np.float32)
y_seq = lstm_labels.transform(y_seq_labels)

# ── 1. MLP Training Curves ────────────────────────────────────────────────────
print("Generating Graph 1: MLP Training Curves...")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle('MLP (Alphabet) — Training Curves', fontsize=15, fontweight='bold', y=1.02)

epochs_mlp = range(1, len(mlp_model.loss_curve_) + 1)

ax1.plot(epochs_mlp, mlp_model.loss_curve_, color=BLUE, linewidth=2.5, label='Train Loss')
ax1.set_title('Training Loss', fontweight='bold')
ax1.set_xlabel('Epoch')
ax1.set_ylabel('Loss')
ax1.legend()

ax2.plot(epochs_mlp, mlp_model.validation_scores_, color=GREEN, linewidth=2.5, label='Val Accuracy')
ax2.axhline(y=max(mlp_model.validation_scores_), color=ORANGE, linestyle='--', alpha=0.7,
            label=f'Best: {max(mlp_model.validation_scores_)*100:.2f}%')
ax2.set_title('Validation Accuracy', fontweight='bold')
ax2.set_xlabel('Epoch')
ax2.set_ylabel('Accuracy')
ax2.set_ylim(0, 1.05)
ax2.legend()

plt.tight_layout()
plt.savefig('graphs/1_mlp_training_curves.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: graphs/1_mlp_training_curves.png")

# ── 2. LSTM Training Curves ───────────────────────────────────────────────────
print("Generating Graph 2: LSTM Training Curves...")
tl = lstm_ckpt.get('train_loss_history', [])
vl = lstm_ckpt.get('val_loss_history', [])
ta = lstm_ckpt.get('train_acc_history', [])
va = lstm_ckpt.get('val_acc_history', [])

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle('LSTM (Phrases) — Training Curves', fontsize=15, fontweight='bold', y=1.02)

epochs_lstm = range(1, len(tl) + 1)

ax1.plot(epochs_lstm, tl, color=BLUE,  linewidth=2.5, label='Train Loss')
ax1.plot(epochs_lstm, vl, color=CYAN,  linewidth=2.5, linestyle='--', label='Val Loss')
ax1.set_title('Loss', fontweight='bold')
ax1.set_xlabel('Epoch')
ax1.set_ylabel('Loss')
ax1.legend()

ax2.plot(epochs_lstm, [x*100 for x in ta], color=GREEN,  linewidth=2.5, label='Train Accuracy')
ax2.plot(epochs_lstm, [x*100 for x in va], color=ORANGE, linewidth=2.5, linestyle='--', label='Val Accuracy')
ax2.axhline(y=max(va)*100, color=RED, linestyle=':', alpha=0.7,
            label=f'Best Val: {max(va)*100:.2f}%')
ax2.set_title('Accuracy', fontweight='bold')
ax2.set_xlabel('Epoch')
ax2.set_ylabel('Accuracy (%)')
ax2.set_ylim(0, 105)
ax2.legend()

plt.tight_layout()
plt.savefig('graphs/2_lstm_training_curves.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: graphs/2_lstm_training_curves.png")

# ── 3. MLP Confusion Matrix ───────────────────────────────────────────────────
print("Generating Graph 3: MLP Confusion Matrix...")
_, X_test, _, y_test = train_test_split(X_alpha, y_alpha, test_size=0.2, random_state=42, stratify=y_alpha)
X_test_sc = mlp_scaler.transform(X_test)
y_pred = mlp_model.predict(X_test_sc)

cm = confusion_matrix(y_test, y_pred)
cm_pct = cm.astype(float) / cm.sum(axis=1, keepdims=True) * 100

fig, ax = plt.subplots(figsize=(16, 13))
sns.heatmap(cm_pct, annot=True, fmt='.0f', cmap='Blues',
            xticklabels=[s.upper() for s in SIGN_NAMES],
            yticklabels=[s.upper() for s in SIGN_NAMES],
            linewidths=0.5, linecolor='#dee2e6',
            cbar_kws={'label': 'Percentage (%)'},
            ax=ax)
ax.set_title('MLP Confusion Matrix — Alphabet Recognition (%)', fontsize=14, fontweight='bold', pad=15)
ax.set_xlabel('Predicted Label', fontsize=11)
ax.set_ylabel('True Label', fontsize=11)
plt.tight_layout()
plt.savefig('graphs/3_mlp_confusion_matrix.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: graphs/3_mlp_confusion_matrix.png")

# ── 4. Per-class Accuracy ─────────────────────────────────────────────────────
print("Generating Graph 4: Per-class Accuracy...")
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12))
fig.suptitle('Per-Class Accuracy', fontsize=15, fontweight='bold')

# MLP per-letter accuracy
report = classification_report(y_test, y_pred, output_dict=True)
alpha_acc = [report[str(i)]['recall'] * 100 for i in range(len(SIGN_NAMES))]
colors_alpha = [GREEN if a >= 95 else ORANGE if a >= 85 else RED for a in alpha_acc]
bars1 = ax1.bar([s.upper() for s in SIGN_NAMES], alpha_acc, color=colors_alpha, edgecolor='white', linewidth=0.5)
ax1.set_title('MLP — Alphabet Per-Letter Accuracy', fontweight='bold')
ax1.set_ylabel('Accuracy (%)')
ax1.set_ylim(0, 110)
ax1.axhline(y=np.mean(alpha_acc), color=BLUE, linestyle='--', linewidth=1.5,
            label=f'Mean: {np.mean(alpha_acc):.1f}%')
for bar, val in zip(bars1, alpha_acc):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
             f'{val:.0f}', ha='center', va='bottom', fontsize=7.5, fontweight='bold')
ax1.legend()

# LSTM per-phrase accuracy
num_classes = len(lstm_labels.classes_)
class LSTMClassifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(126, 128, 2, batch_first=True, dropout=0.3)
        self.dropout = nn.Dropout(0.3)
        self.fc = nn.Linear(128, num_classes)
    def forward(self, x):
        _, (h, _) = self.lstm(x)
        return self.fc(self.dropout(h[-1]))

lstm_net = LSTMClassifier()
lstm_net.load_state_dict(lstm_ckpt['model_state'])
lstm_net.eval()

with torch.no_grad():
    logits = lstm_net(torch.tensor(X_seq))
    y_pred_lstm = logits.argmax(dim=1).numpy()

lstm_report = classification_report(y_seq, y_pred_lstm, output_dict=True)
phrase_labels_display = [PHRASE_DISPLAY.get(p, p) for p in lstm_labels.classes_]
phrase_acc = [lstm_report[str(i)]['recall'] * 100 for i in range(num_classes)]
colors_phrase = [GREEN if a >= 95 else ORANGE if a >= 85 else RED for a in phrase_acc]
bars2 = ax2.bar(phrase_labels_display, phrase_acc, color=colors_phrase, edgecolor='white', linewidth=0.5)
ax2.set_title('LSTM — Phrase Per-Class Accuracy', fontweight='bold')
ax2.set_ylabel('Accuracy (%)')
ax2.set_ylim(0, 115)
ax2.axhline(y=np.mean(phrase_acc), color=BLUE, linestyle='--', linewidth=1.5,
            label=f'Mean: {np.mean(phrase_acc):.1f}%')
for bar, val in zip(bars2, phrase_acc):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
             f'{val:.0f}%', ha='center', va='bottom', fontsize=8.5, fontweight='bold')
ax2.tick_params(axis='x', rotation=20)
ax2.legend()

# Legend for colors
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor=GREEN, label='≥ 95%'),
                   Patch(facecolor=ORANGE, label='85–94%'),
                   Patch(facecolor=RED, label='< 85%')]
fig.legend(handles=legend_elements, loc='lower center', ncol=3, fontsize=10,
           bbox_to_anchor=(0.5, -0.02))

plt.tight_layout()
plt.savefig('graphs/4_per_class_accuracy.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: graphs/4_per_class_accuracy.png")

# ── 5. Dataset Distribution ───────────────────────────────────────────────────
print("Generating Graph 5: Dataset Distribution...")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
fig.suptitle('Dataset Distribution', fontsize=15, fontweight='bold')

# Alphabet counts
alpha_counts = []
for sign in SIGN_NAMES:
    path = os.path.join('data', sign)
    alpha_counts.append(len([f for f in os.listdir(path) if f.endswith('.npy')]))

ax1.bar([s.upper() for s in SIGN_NAMES], alpha_counts,
        color=BLUE, alpha=0.85, edgecolor='white')
ax1.axhline(y=np.mean(alpha_counts), color=ORANGE, linestyle='--', linewidth=1.5,
            label=f'Mean: {np.mean(alpha_counts):.0f}')
ax1.set_title(f'Alphabet Dataset  (Total: {sum(alpha_counts):,} samples)', fontweight='bold')
ax1.set_ylabel('Number of Samples')
ax1.set_xlabel('Letter')
ax1.legend()

# Phrase counts
phrase_counts = []
phrase_display_list = []
for sign in PHRASE_NAMES:
    path = os.path.join('data', 'sequences', sign)
    cnt = len([f for f in os.listdir(path) if f.endswith('.npy')]) if os.path.exists(path) else 0
    phrase_counts.append(cnt)
    phrase_display_list.append(PHRASE_DISPLAY.get(sign, sign))

ax2.barh(phrase_display_list, phrase_counts,
         color=CYAN, alpha=0.85, edgecolor='white')
ax2.axvline(x=np.mean(phrase_counts), color=ORANGE, linestyle='--', linewidth=1.5,
            label=f'Mean: {np.mean(phrase_counts):.0f}')
for i, (val, label) in enumerate(zip(phrase_counts, phrase_display_list)):
    ax2.text(val + 1, i, str(val), va='center', fontsize=9, fontweight='bold')
ax2.set_title(f'Phrase Dataset  (Total: {sum(phrase_counts):,} sequences)', fontweight='bold')
ax2.set_xlabel('Number of Sequences')
ax2.legend()

plt.tight_layout()
plt.savefig('graphs/5_dataset_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: graphs/5_dataset_distribution.png")

# ── 6. Confidence Score Distribution ─────────────────────────────────────────
print("Generating Graph 6: Confidence Score Distribution...")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle('Confidence Score Distribution', fontsize=15, fontweight='bold')

# MLP confidence on test set
X_test_sc2 = mlp_scaler.transform(X_test)
mlp_probs = mlp_model.predict_proba(X_test_sc2)
mlp_conf = np.max(mlp_probs, axis=1) * 100

ax1.hist(mlp_conf, bins=40, color=BLUE, alpha=0.8, edgecolor='white', linewidth=0.5)
ax1.axvline(x=np.mean(mlp_conf), color=ORANGE, linestyle='--', linewidth=2,
            label=f'Mean: {np.mean(mlp_conf):.1f}%')
ax1.axvline(x=90, color=RED, linestyle=':', linewidth=1.5, label='Threshold: 90%')
ax1.set_title('MLP — Alphabet Confidence', fontweight='bold')
ax1.set_xlabel('Confidence (%)')
ax1.set_ylabel('Number of Samples')
ax1.legend()

# LSTM confidence on full dataset
with torch.no_grad():
    logits_all = lstm_net(torch.tensor(X_seq))
    probs_all = torch.softmax(logits_all, dim=1).numpy()
lstm_conf = np.max(probs_all, axis=1) * 100

ax2.hist(lstm_conf, bins=30, color=CYAN, alpha=0.8, edgecolor='white', linewidth=0.5)
ax2.axvline(x=np.mean(lstm_conf), color=ORANGE, linestyle='--', linewidth=2,
            label=f'Mean: {np.mean(lstm_conf):.1f}%')
ax2.axvline(x=85, color=RED, linestyle=':', linewidth=1.5, label='Threshold: 85%')
ax2.set_title('LSTM — Phrase Confidence', fontweight='bold')
ax2.set_xlabel('Confidence (%)')
ax2.set_ylabel('Number of Sequences')
ax2.legend()

plt.tight_layout()
plt.savefig('graphs/6_confidence_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: graphs/6_confidence_distribution.png")

# ── Done ──────────────────────────────────────────────────────────────────────
print("\n✓ All graphs saved to graphs/ folder:")
for f in sorted(os.listdir('graphs')):
    print(f"  graphs/{f}")
