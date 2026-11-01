# Reference timeline

Times are film seconds. "Change" values are mean per-frame absolute luma difference at 4fps sampling,
so they describe how much the whole picture moved at a moment, not what appeared.

| Time | Measured change | Reading |
| --- | --- | --- |
| 0.00 - 7.25 | rising from 0.005 to 0.06 | Establish. Slow movement on a near-black ground. |
| 7.25 | 0.0615 | First reset inside the graphic. |
| 15.25 | 0.1185 (peak) | The largest single change in the piece. |
| 19.25 | 0.0831 | Second reset. |
| 19.25 - 38.00 | low, 0.005-0.01 | Sustained development with no reset. |
| 38.00 | 0.0819 | Opens the dense passage. |
| 40.75 | 0.0947 | |
| 44.75 | 0.0715 | |
| 47.50 | 0.0817 | |
| 50.25 | 0.0833 | |
| 52.75 | 0.0794 | Closes the dense passage, ~15s long. |
| 52.75 - 69.50 | low | Long settling development. |
| 69.50 | 0.0803 | Opens the second half. |
| 71.75 | 0.0962 | |
| 71.75 - 143.25 | low | The longest stretch with no reset (71.5s). |
| 143.25 | 0.0679 | Close. |

Bottom band bright-pixel share stays near 2.72% across the piece, so the persistent text line is
present throughout rather than appearing only in places. Top band remains near 0.89%.

Beat grid: 112.35 BPM, first strong onset near 0.255s, period 0.534s. Useful accent instants are
`0.255 + n * 0.534`. The soundtrack is 146.355s, which bounds any film that uses it.
