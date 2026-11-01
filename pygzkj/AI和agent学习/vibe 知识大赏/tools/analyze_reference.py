"""Measure a reference video from its sampled frames.

Reads the JPEG sequence dumped at a fixed fps and reports shot cuts, palette,
brightness and motion, so the piece can be described without watching it.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

FPS = 4.0


def load(seq_dir: Path) -> tuple[np.ndarray, np.ndarray]:
    files = sorted(seq_dir.glob("f_*.jpg"))
    rgb = []
    gray = []
    for f in files:
        im = Image.open(f).convert("RGB")
        a = np.asarray(im, dtype=np.float32) / 255.0
        rgb.append(a)
        gray.append(a @ np.array([0.299, 0.587, 0.114], dtype=np.float32))
    return np.stack(rgb), np.stack(gray)


def hist(frames: np.ndarray, bins: int = 16) -> np.ndarray:
    out = []
    for a in frames:
        h, _ = np.histogramdd(
            a.reshape(-1, 3),
            bins=(bins, bins, bins),
            range=((0, 1), (0, 1), (0, 1)),
        )
        h = h.ravel()
        out.append(h / (h.sum() + 1e-9))
    return np.stack(out)


def cut_points(h: np.ndarray, gray: np.ndarray) -> list[int]:
    inter = np.minimum(h[1:], h[:-1]).sum(axis=1)
    dist = 1.0 - inter
    motion = np.abs(np.diff(gray, axis=0)).mean(axis=(1, 2))
    # a cut is a large palette change that is not explained by gradual motion
    score = dist / (motion + 1e-4)
    thr = dist.mean() + 2.5 * dist.std()
    cand = [i + 1 for i in range(len(dist)) if dist[i] > thr and score[i] > 60]
    merged: list[int] = []
    for c in cand:
        if merged and c - merged[-1] < 3:
            continue
        merged.append(c)
    return merged


def scene_changes(gray: np.ndarray, k: float = 3.0) -> list[tuple[float, float]]:
    """Group frames whose change from the previous frame spikes above noise."""
    motion = np.abs(np.diff(gray, axis=0)).mean(axis=(1, 2))
    thr = motion.mean() + k * motion.std()
    hits = np.where(motion > thr)[0]
    groups: list[list[int]] = []
    for i in hits:
        if groups and i - groups[-1][-1] <= 3:
            groups[-1].append(i)
        else:
            groups.append([i])
    out = []
    for g in groups:
        peak = g[int(np.argmax(motion[g]))] + 1
        out.append((peak / FPS, float(motion[g].max())))
    return out


def band_activity(gray: np.ndarray) -> dict[str, float]:
    """Bright-pixel share of the lower caption band vs the upper label band."""
    h = gray.shape[1]
    top = gray[:, : int(h * 0.12), :]
    bottom = gray[:, int(h * 0.86):, :]
    return {
        "top_band": float((top > 0.5).mean()),
        "bottom_band": float((bottom > 0.5).mean()),
    }


def palette(frames: np.ndarray, k: int = 6) -> list[tuple[str, float]]:
    flat = (frames.reshape(-1, 3) * 255).astype(np.uint8)
    im = Image.fromarray(flat.reshape(1, -1, 3))
    q = im.quantize(colors=k, method=Image.MEDIANCUT)
    counts = np.bincount(np.asarray(q).ravel(), minlength=k)
    pal = np.array(q.getpalette()[: k * 3]).reshape(k, 3)
    order = np.argsort(-counts)
    return [
        ("#%02X%02X%02X" % tuple(pal[i]), counts[i] / counts.sum())
        for i in order
    ]


def main() -> None:
    seq = Path(sys.argv[1])
    frames, gray = load(seq)
    n = len(frames)
    print(f"sampled frames : {n}  ({n / FPS:.1f}s at {FPS:g} fps)")

    bright = gray.mean(axis=(1, 2))
    print(f"brightness     : mean {bright.mean():.3f}  min {bright.min():.3f}  max {bright.max():.3f}")

    motion = np.abs(np.diff(gray, axis=0)).mean(axis=(1, 2))
    print(f"motion/frame   : mean {motion.mean():.4f}  median {np.median(motion):.4f}  max {motion.max():.4f}")

    h = hist(frames)
    cuts = cut_points(h, gray)
    times = [c / FPS for c in cuts]
    print(f"shots          : {len(cuts) + 1}")
    if len(cuts) < 3:
        print("  (palette-based cuts found nothing; using motion spikes instead)")
        spikes = scene_changes(gray)
        print(f"motion spikes  : {len(spikes)}")
        for t, m in spikes:
            print(f"  {t:7.2f}s  change {m:.4f}")
        times = [t for t, _ in spikes]
    if times:
        gaps = np.diff([0.0] + times + [n / FPS])
        print(f"shot length    : mean {gaps.mean():.2f}s  median {np.median(gaps):.2f}s  min {gaps.min():.2f}s  max {gaps.max():.2f}s")
        print(f"cut times (s)  : {[round(t, 2) for t in times]}")

    for name, value in band_activity(gray).items():
        print(f"{name:14s} : {value * 100:.2f}% pixels above 0.5")

    print("palette        :")
    for hexv, share in palette(frames):
        print(f"  {hexv}  {share * 100:5.1f}%")

    # brightness over time, in 10 even slices
    print("brightness by tenth:")
    step = max(1, n // 10)
    for i in range(0, n, step):
        chunk = bright[i:i + step]
        print(f"  {i / FPS:6.1f}s  {chunk.mean():.3f}")


if __name__ == "__main__":
    main()
