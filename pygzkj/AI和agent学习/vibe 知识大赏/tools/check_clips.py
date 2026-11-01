"""Compact frame-level check of rendered clips: exposure, palette and text bands."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image


def frames(ffmpeg: str, video: Path, out: Path, fps: float = 2.0) -> list[Path]:
    subprocess.run(
        [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(video),
         "-vf", f"fps={fps},scale=320:-2", "-q:v", "3", str(out / "f_%04d.jpg")],
        check=True,
    )
    return sorted(out.glob("f_*.jpg"))


def main() -> None:
    ffmpeg = sys.argv[1]
    videos = [Path(p) for p in sys.argv[2:]]
    print(f"{'clip':<16}{'frames':>7}{'bright':>9}{'motion':>9}{'topband':>9}{'botband':>9}  palette")
    for video in videos:
        tmp = Path(tempfile.mkdtemp())
        try:
            files = frames(ffmpeg, video, tmp)
            rgb, gray = [], []
            for f in files:
                a = np.asarray(Image.open(f).convert("RGB"), dtype=np.float32) / 255.0
                rgb.append(a)
                gray.append(a @ np.array([0.299, 0.587, 0.114], dtype=np.float32))
            rgb = np.stack(rgb)
            gray = np.stack(gray)
            h = gray.shape[1]
            top = float((gray[:, : int(h * 0.12), :] > 0.5).mean())
            bottom = float((gray[:, int(h * 0.86):, :] > 0.5).mean())
            motion = float(np.abs(np.diff(gray, axis=0)).mean())

            flat = (rgb.reshape(-1, 3) * 255).astype(np.uint8)
            im = Image.fromarray(flat.reshape(1, -1, 3))
            q = im.quantize(colors=5, method=Image.MEDIANCUT)
            counts = np.bincount(np.asarray(q).ravel(), minlength=5)
            pal = np.array(q.getpalette()[:15]).reshape(5, 3)
            order = np.argsort(-counts)
            swatch = " ".join("#%02X%02X%02X" % tuple(pal[i]) for i in order[:4])

            print(f"{video.stem:<16}{len(files):>7}{gray.mean():>9.3f}{motion:>9.4f}"
                  f"{top:>8.2f}%{bottom:>8.2f}%  {swatch}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
