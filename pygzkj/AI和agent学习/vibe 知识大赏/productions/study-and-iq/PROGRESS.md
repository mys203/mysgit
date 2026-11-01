# Progress

## State

The film is delivered.

| Thing | State |
| --- | --- |
| Result | `results/学习与智商-组块.mp4` — 1920x1080, 30fps, h264 + aac, 146.433s, 16.4 MB |
| Build | `bld_20261011T163052425Z_3766C54136` |
| Angle | Accepted by the user: 专家不是脑子更大，是组块更多 |
| Component | `packages/study-iq-scene`, built to `dist/`, installed as a `file:` dependency |
| Beat grid | 112.35 BPM, 274 accents, generated into `packages/study-iq-scene/src/beats.ts` |
| Cost | zero. Every request ran on `media.local` and `html.local`. |

## Environment, resolved

| Thing | State |
| --- | --- |
| `hypit` Skill | installed, `~/.codex/skills/hypit` |
| `hypit` executable | installed, `@hypit/hypit` 0.3.1, global npm |
| ffmpeg / ffprobe | ffmpeg 6.1.1 (`ffmpeg-static`) and ffprobe 2023, explicit paths in the Profile |
| Render browser | managed Chrome for Testing 152.0.7928.2 under `~/.cache/hypit/html-rasterizer/chrome`, fetched from the npmmirror binary mirror |
| Unused endpoints | `hypihub.default` (no credential) and `image.opencv.local` (not prepared). Neither is required for local rendering; both still report as diagnostics. |

## What the next edit should know

- Visual IR style values need units; bare numbers are dropped and collapse the element.
- Exact fonts reject `font-weight` in the element style; weight comes from wrapper CSS.
- The `hypit get --to` export refuses to overwrite. Delete the destination first.
- `git clone` to github.com fails on this machine. npm, PowerShell HTTP, the skill-installer
  download path and the npmmirror binary mirror all work.
- `hypit` runs from the project directory; the launcher is `%APPDATA%\npm\hypit.cmd`.
