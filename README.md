# Store Camera Analytics

Store analytics case study (ML Engineer, computer vision): person detection and tracking, door IN/OUT counting, queue and counter zones with alerts, on several video streams at once.

All footage is public and licensed for download, processing and display. No private or company footage is used.

## Quick start

Requirements: Python 3.11, `make`, `curl`. Tested on macOS (Apple M1).

```bash
make run
```

The first run creates `.venv`, installs the pinned packages, downloads the videos (~310 MB) and the model (5 MB), then starts all cameras. Stop with Ctrl+C.

| Command | What it does |
|---|---|
| `make run` | install + download (first time only), then start all cameras |
| `make run ARGS="--duration 300"` | same, but stop after 300 seconds |
| `make test` | unit tests for the door counter, zones and alerts |
| `make download` | only download videos and weights |

**Not on a Mac?** Set `model.device` in `config.yaml` to `cpu` or `cuda:0`.

### Outputs (in `outputs/`)

- `<camera>_minutes.csv`: one row per minute with `minute, in, out, avg_queue, max_queue, empty_counter_seconds`. Columns a camera does not have stay empty.
- `alerts.jsonl`: one JSON line per alert event, for example
  `{"camera": "counter", "alert": "queue", "event": "end", "start": "2026-11-06 21:52:41", "end": "2026-11-06 21:54:30", "peak": 6}`

## How it works

```
config.yaml ──► app/main.py starts one thread per camera (app/camera.py)
                   │
   each thread:  read frame ──► YOLO11n + ByteTrack (app/tracking.py) ──► people with IDs
                   │
                   ├── app/line_counter.py   IN / OUT at the door line
                   ├── app/zones.py          people in queue / staff zone, once per second
                   ├── app/alerts.py         queue alert, empty-counter alert
                   └── app/report.py         minute CSV + alerts.jsonl
```

- Every line, zone and threshold is in `config.yaml`.
- A video file is played at real-time speed, like a live camera; when processing is slower, frames are skipped.
- If a source cannot be opened or drops, its thread waits `reconnect_seconds` and tries again. The other cameras are not affected.

### Tools

| Tool | Use |
|---|---|
| `tools/draw_zones.py <video> --second 30` | click points on a frame to get coordinates for the config |
| `tools/show_config.py` | draw the configured line and zones on a frame of each camera |
| `tools/track_preview.py <camera> --seconds 300` | offline run of one camera: video with boxes and IDs, crossings and alerts printed, per-second zone values saved |

## Video sources and licences

Videos are **not stored in this repository**; `scripts/download.sh` downloads them.

All three clips come from the **MEVA dataset** (Multiview Extended Video with Activities):

- **Author:** Kitware Inc. and the Intelligence Advanced Research Projects Activity (IARPA), https://mevadata.org/
- **Licence:** Creative Commons Attribution 4.0 International (CC BY 4.0), https://creativecommons.org/licenses/by/4.0/ (MEVA licence text: https://mevadata.org/resources/MEVA-data-license.txt)
- **Reference door labels:** MEVA activity annotations from https://gitlab.kitware.com/meva/meva-data-repo, saved in `labels/meva_reference_entrance.csv`.

| Camera in config | Source URL | Content | Timestamps used |
|---|---|---|---|
| `entrance` | https://mevadata-public-01.s3.amazonaws.com/drops-123-r13/2018-03-09/10/2018-03-09.10-40-01.10-45-01.school.G420.r13.avi | Entrance doors, people entering and leaving | 00:00–05:00 (full clip) |
| `counter` | https://mevadata-public-01.s3.amazonaws.com/drops-123-r13/2018-03-07/17/2018-03-07.17-20-00.17-25-00.school.G421.r13.avi | Coffee counter with a queue | 00:00–05:00 (full clip) |
| `counter_morning` | https://mevadata-public-01.s3.amazonaws.com/drops-123-r13/2018-03-07/11/2018-03-07.11-10-01.11-15-01.school.G421.r13.avi | Same counter, zoomed out; the server leaves the counter at times | 00:00–05:00 (full clip) |

All clips: 1920×1072, 30 fps, 5 minutes each (15 minutes in total).

Other clips looked at but not used: Pexels clips by Casey Whalen (too short) and CAVIAR shop-entrance clips (384×288, very few people).

## Known failure cases

Timestamps are video time in each clip. "Fixed" means the config or code was changed and the case was checked again.

| Clip | Time | What happens | Why | Status |
|---|---|---|---|---|
| counter | 00:46–00:53 | Person `#416` waiting in the queue is not counted | Hidden behind the person in front; no box, or a box cut off above the feet | Open (occlusion) |
| counter | 01:13–01:22 | Same person, now `#559`, not counted | Same occlusion; she also got a new ID | Open (occlusion, ID switch) |
| counter | 02:12–02:18 | One person gets three IDs: `#708`, `#746`, `#722` | ByteTrack loses the person in a crowd and starts new tracks | Open. The queue count is per frame, so it is not affected; a per-person waiting time would be |
| counter | 02:25–02:32, 03:23–03:28 | Staff zone shows 0 while the server is there | Server is cut off by the bottom of the picture and half hidden by the table; YOLO misses her | Open. No alert (shorter than 10 s), but these seconds are counted in `empty_counter_seconds` |
| counter | 03:40 | Staff zone shows 2 people (`#1209`) | A seated person behind the coffee urn gets a box cut off by the urn, so the foot point lands in the staff zone | Fixed: staff zone top edge moved down to y = 800 |
| counter | whole clip | Customer being served was not counted in the queue | Legs cut off by the bottom of the picture, so the foot point sits at the very bottom edge, just below the zone | Fixed: queue zone reaches the bottom edge |
| counter_morning | 00:00–00:13, 01:22–01:28 | Staff zone shows 0 while the server is there | Server is bent over behind the counter; YOLO misses the pose | Open. Gave a false empty-counter alert with an earlier queue zone |
| counter_morning | whole clip | People sitting at the café tables were counted in the queue | Queue zone top edge touched the tables | Fixed: top edge moved down 60 px |
| counter_morning | 00:45 | Staff member (pink top) walking through the queue zone is counted as a customer | No staff / customer distinction | Open |
| entrance | whole clip | OUT 43 vs 59 in MEVA labels | Groups leave together and hide each other | Open (occlusion) |
| entrance | first line position | People counted OUT 23 of 59 | Line too close to the door: people disappear through it before they are clearly on the other side | Fixed: line moved further from the door |
| entrance | 00:04–00:12 (old clip) | Same person counted OUT, IN, OUT, IN | Legs hidden by others, so the box gets shorter and the foot point jumps over the line | Fixed: person must stay on the new side for `min_seconds` (0.15 s) |
| entrance | live run, 3 cameras | `#481` counted OUT, IN, OUT within 11 s | At 3–4 fps (laptop under load) the foot point moves in big steps | Partly fixed: `min_seconds` instead of frames, so the rule means the same at any fps |

## Privacy

- No face recognition and no attempt to identify anyone. The system only detects and tracks anonymous person boxes.
- Faces are blurred in every published output frame, GIF or video.
