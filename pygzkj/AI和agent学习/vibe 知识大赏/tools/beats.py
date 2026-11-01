"""Onset/tempo analysis for the extracted reference soundtrack.

Reads a mono 16-bit WAV, builds a spectral-flux onset envelope, estimates the
tempo by autocorrelation, then peak-picks beat positions.
"""

from __future__ import annotations

import json
import sys
import wave

import numpy as np

N_FFT = 1024
HOP = 512


def read_wav(path: str) -> tuple[np.ndarray, int]:
    with wave.open(path, "rb") as w:
        if w.getsampwidth() != 2:
            raise SystemExit("expected 16-bit PCM wav")
        sr = w.getframerate()
        raw = w.readframes(w.getnframes())
    return np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0, sr


def stft_mag(x: np.ndarray) -> np.ndarray:
    window = np.hanning(N_FFT)
    n_frames = max(0, 1 + (len(x) - N_FFT) // HOP)
    frames = np.lib.stride_tricks.as_strided(
        x,
        shape=(n_frames, N_FFT),
        strides=(x.strides[0] * HOP, x.strides[0]),
    )
    return np.abs(np.fft.rfft(frames * window, axis=1))


def onset_envelope(mag: np.ndarray) -> np.ndarray:
    # log compression keeps quiet percussive hits visible
    log_mag = np.log1p(1000.0 * mag)
    flux = np.diff(log_mag, axis=0)
    flux = np.maximum(flux, 0.0).sum(axis=1)
    flux -= flux.mean()
    # 3-frame moving average to tame single-bin noise
    kernel = np.ones(3) / 3.0
    return np.convolve(flux, kernel, mode="same")


def estimate_tempo(env: np.ndarray, fps: float, lo=70.0, hi=180.0) -> tuple[float, float]:
    env = env - env.mean()
    ac = np.correlate(env, env, mode="full")[len(env) - 1:]
    ac /= ac[0] + 1e-12
    min_lag = int(round(fps * 60.0 / hi))
    max_lag = int(round(fps * 60.0 / lo))
    span = ac[min_lag:max_lag + 1]
    best_lag = min_lag + int(np.argmax(span))
    bpm = 60.0 * fps / best_lag
    # strength = how far the winning peak stands above the local mean
    strength = float(span.max() / (span.mean() + 1e-12))
    return bpm, strength


def pick_beats(env: np.ndarray, fps: float, period_frames: float) -> list[int]:
    threshold = env.mean() + 0.6 * env.std()
    beats: list[int] = []
    i = 1
    min_gap = max(2, int(period_frames * 0.45))
    while i < len(env) - 1:
        if env[i] >= threshold and env[i] >= env[i - 1] and env[i] > env[i + 1]:
            if not beats or i - beats[-1] >= min_gap:
                beats.append(i)
            elif env[i] > env[beats[-1]]:
                beats[-1] = i
        i += 1
    return beats


def main() -> None:
    wav_path = sys.argv[1]
    x, sr = read_wav(wav_path)
    mag = stft_mag(x)
    env = onset_envelope(mag)
    fps = sr / HOP

    bpm, strength = estimate_tempo(env, fps)
    period = 60.0 * fps / bpm
    beats = pick_beats(env, fps, period)

    times = [round(b / fps, 3) for b in beats]
    gaps = np.diff(times) if len(times) > 1 else np.array([0.0])

    print(f"duration      : {len(x) / sr:.3f}s")
    print(f"tempo         : {bpm:.2f} BPM (period {60 / bpm:.3f}s, strength {strength:.2f})")
    print(f"detected beats: {len(times)}")
    if len(times) > 1:
        print(f"beat spacing  : mean {gaps.mean():.3f}s  median {np.median(gaps):.3f}s  sd {gaps.std():.3f}s")
        print(f"first 24      : {times[:24]}")

    out = {"duration": len(x) / sr, "bpm": round(bpm, 3), "beats": times}
    with open(wav_path.replace(".wav", "_beats.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print("written       : " + wav_path.replace(".wav", "_beats.json"))


if __name__ == "__main__":
    main()
