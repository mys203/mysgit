# Reference: 参考视频.mp4 (Vibe 知识大赏 风格知识短片)

Supplied at `../../参考视频.mp4`. 1280x720, 30fps, 2:26.354, H.264 + AAC 44.1kHz stereo.
Source comment tag `vid:v0200fg10000datigcvog65t428aod70` indicates a Douyin download.

## How this reading was made

The piece was measured from its own bytes, not watched frame by frame with a viewing model:
`tools/analyze_reference.py` samples it at 4fps and reports palette, brightness, motion, band
activity and change points; `tools/beats.py` reads the extracted soundtrack. Statements below are
measurements unless marked as interpretation.

## What the piece is

A single continuous graphic composition, not an edited film. Over 146 seconds the picture never
leaves one dark field; measured palette change never produces a cut.

| Measured | Value |
| --- | --- |
| Mean brightness | 0.131 (range 0.061 - 0.242) |
| Mean per-frame motion | 0.0114 (median 0.0058, peak 0.1185) |
| Dominant palette | `#1B1D3C` 26.7%, `#13132E` 26.0%, `#0F0D1F` 15.6%, `#0A0A17` 10.9%, `#5A566A` 10.7%, `#060814` 10.0% |
| Bottom band (below 86% height) bright pixels | 2.72% |
| Top band (above 12% height) bright pixels | 0.89% |

**Interpretation.** The palette is a narrow family of near-black blues; the only light values are
text and thin graphic strokes. Motion is low but never zero, so attention is held by continuous
change on an essentially unchanging ground. The bottom band carries roughly three times the bright
pixel share of the top band, consistent with a subtitle line below a smaller label.

## Structure

No palette-based cuts exist, so change points were taken from motion spikes:

`7.25s · 15.25s · 19.25s · 38.00s · 40.75s · 44.75s · 47.50s · 50.25s · 52.75s · 69.50s · 71.75s · 143.25s`

**Interpretation.** Long stretches without a spike are stretches where the graphic keeps evolving
without a hard reset. The cluster between 38s and 53s is the densest section of the piece: a run of
roughly 2-4 second graphic changes. The two spikes at 69.5s and 71.75s open the second half, and
143.25s closes it. So the piece reads as: a slow establishing passage, a dense middle argument, a
longer settling passage, and a short close.

## Sound

Extracted with `tools/beats.py` from a 22050 Hz mono reduction of the soundtrack.

| Measured | Value |
| --- | --- |
| Tempo | 112.35 BPM (period 0.534s), autocorrelation strength 31.71 |
| Onset peaks | 413 over 146.4s |

**Interpretation.** The dominant tempo is strong and unambiguous, so a beat grid at 112.35 BPM is a
defensible basis for cutting. The high onset count shows the surface is dense with secondary
percussive and textural events, so a film cut to every detected onset would be far busier than the
reference, whose own motion stays low. The useful reading is: cut accents to the beat, keep the
picture's motion underneath it.

## Reusable facts for the target

- One continuous dark field; change happens inside it rather than by cutting between scenes.
- Near-black blue ground, light type, one warm accent at most.
- A persistent bottom text line carries the argument; the top carries identity.
- 112.35 BPM gives the accent grid; accents should be sparser than the onset stream.
- Reference length 146.35s, which is exactly the length of the extracted soundtrack.
