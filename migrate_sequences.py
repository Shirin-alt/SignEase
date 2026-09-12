"""
Converts existing (30, 126) sequence .npy files to (30, 252) by appending
per-frame velocity (delta of normalized landmarks) as additional features.
Overwrites files in-place. Safe to re-run — skips already-migrated files.
"""
import numpy as np
import os

DATA_PATH = os.path.join('data', 'sequences')

def normalize_hand(flat63):
    pts = flat63.reshape(21, 3)
    pts = pts - pts[0]
    scale = np.max(np.abs(pts))
    if scale > 0:
        pts = pts / scale
    return pts.flatten()

def normalize_sequence(seq126):
    """Normalize each frame's landmarks (wrist-relative + scale)."""
    out = np.zeros_like(seq126)
    for i, frame in enumerate(seq126):
        h1 = normalize_hand(frame[:63])
        h2 = normalize_hand(frame[63:])
        out[i] = np.concatenate([h1, h2])
    return out

def add_velocity(norm_seq):
    """Append velocity (frame[t] - frame[t-1]) to each frame -> (30, 252)."""
    T = len(norm_seq)
    result = np.zeros((T, 252), dtype=np.float32)
    for i in range(T):
        landmarks = norm_seq[i]
        velocity = norm_seq[i] - norm_seq[i - 1] if i > 0 else np.zeros(126)
        result[i] = np.concatenate([landmarks, velocity])
    return result

converted = 0
skipped = 0

for sign in os.listdir(DATA_PATH):
    sign_path = os.path.join(DATA_PATH, sign)
    if not os.path.isdir(sign_path):
        continue
    for fname in os.listdir(sign_path):
        if not fname.endswith('.npy'):
            continue
        fpath = os.path.join(sign_path, fname)
        seq = np.load(fpath)
        if seq.shape == (30, 252):
            skipped += 1
            continue
        if seq.shape != (30, 126):
            print(f"  Unexpected shape {seq.shape} in {fpath}, skipping.")
            continue
        norm = normalize_sequence(seq)
        upgraded = add_velocity(norm)
        np.save(fpath, upgraded)
        converted += 1

print(f"Done. Converted: {converted}  Already up-to-date: {skipped}")
