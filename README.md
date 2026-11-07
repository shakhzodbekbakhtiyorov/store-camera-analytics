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
| `tools/track_preview.py <camera> --seconds 300` | offline run of one camera: video with boxes and IDs, crossings and alerts printed; crossings and per-second zone values saved as CSV |

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

## Measurements

### Door IN/OUT (entrance clip)

Reference: MEVA's own activity labels for this clip (`person_enters_scene_through_structure` / `person_exits_scene_through_structure`), saved in `labels/meva_reference_entrance.csv`. System crossings come from `tools/track_preview.py entrance --seconds 300` (30 fps, every frame).

```bash
python tools/evaluate_door.py labels/meva_reference_entrance.csv outputs/entrance_crossings.csv
```

A label counts as **found** if the system has a crossing in the same direction within the labelled time ±2 s. A system crossing that matches no label is **false**.

| Direction | MEVA labels | System | Found | Missed | False |
|---|---|---|---|---|---|
| IN | 13 | 15 | 13 | 0 | 2 (01:50.7, 03:34.2) |
| OUT | 59 | 44 | 43 | 16 | 1 (01:45.2) |

- IN is complete; OUT finds 43 of 59 (73%), and almost every OUT the system reports is real (43 of 44).
- The misses come in groups: 00:48–00:49, 01:01–01:04 and 01:16–01:21. These are groups of people leaving together and hiding each other, so the tracker loses some of them before the line.
- At 03:33–03:34 `#920` is counted OUT and then IN 1.1 s later: the foot point jumps back over the line in a group. That gives one false IN, and the second person leaving at 03:34.5 is missed.
- At lower frame rates the totals barely change: 14 IN / 42 OUT at 10 fps, 13 / 39 at 5 fps.

### Queue length (counter clip)

I paused `outputs/track_counter.mp4` every 10 s and counted the people waiting by hand, from 00:10 to 04:50 (29 labels, in `labels/counter_queue_hand.csv`). The system value is the per-second queue from `tools/track_preview.py counter --seconds 300`.

```bash
python tools/evaluate_queue.py labels/counter_queue_hand.csv outputs/counter_seconds.csv
```

| Labels | MAE | Exact | Max error |
|---|---|---|---|
| 29 (every 10 s, 00:10–04:50) | **0.31 people** | 21 / 29 | 2 |

Where the 8 errors come from:

| Time | Hand | System | Cause |
|---|---|---|---|
| 00:50, 01:20, 01:30, 01:40 | 6, 5, 5, 5 | 5, 4, 4, 4 | One person hidden behind another (occlusion) |
| 02:10 | 4 | 6 | One person detected as three overlapping boxes |
| 00:20, 03:20, 04:40 | 3, 3, 2 | 4, 4, 3 | Someone walking through the queue zone, not waiting |

The 05:00 label is left out: it is the last frame of the clip, and the system has no complete second there.

People walking through the queue zone are counted as errors: the queue means people **waiting**, and the hand labels count only them. A possible fix is a minimum time in the zone (for example 3 s) before a person counts; it is not implemented.

### Alerts

Expected alerts come from the hand labels above (queue alert: 3 or more people for 15 s or more) and from watching the staff zone in the videos (empty-counter alert: no server for 10 s while someone waits).

| Clip | Alert | Expected | Found by the system | Missed | False |
|---|---|---|---|---|---|
| counter | queue | 2: about 00:20–02:40 and 03:00–04:00 | 2: 00:11–02:48 (peak 7), 02:52–04:16 (peak 4) | 0 | 0 |
| counter | empty counter | 0 (server always there) | 0 | 0 | 0 |
| counter_morning | queue | 0 (3 or more people for about 12 s only) | 0 | 0 | 0 |
| counter_morning | empty counter | 0 (server away 8 s at most) | 0 | 0 | 0 |

Start and end times differ from the labels by up to ~10 s, because the labels are only every 10 s.

Limits: these clips have no real empty-counter alert, so this alert is tested only by the unit tests (`tests/test_zones_alerts.py`). With an earlier queue zone, `counter_morning` gave one false empty-counter alert (server bent over and missed by YOLO, see failure cases).

### Speed

**Hardware:** MacBook Air M1 (2020, 8-core CPU, 7-core GPU, fanless), on AC power. **Model:** YOLO11n (`yolo11n.pt`, 5.6 MB, 2.6 M parameters), PyTorch on the Apple GPU (`device: mps`), FP32. **Input:** 1920×1072 video at 30 fps, resized by YOLO to 640 px on the long side. Tracker: ByteTrack.

| Run | Streams | FPS per stream | Total FPS |
|---|---|---|---|
| 1 camera, as fast as possible (`tools/track_preview.py`, 60 s of video, includes drawing and writing the output video) | 1 | 35.5 (entrance), 31.5 (counter, more people) | 31–36 |
| Live service, all 3 cameras at once (`python -m app.main --duration 120`, steady state after warm-up) | 3 | 12.4–13.3 | 37–40 |

- One camera keeps up with a 30 fps source in real time.
- With 3 cameras the total stays about the same (~38 FPS): the cameras share one GPU and the CPU decodes three 1080p videos. Each camera then processes ~13 of its 30 frames per second and skips the rest (as a live stream would).
- Door counting still works at this rate: on the entrance clip, 10 fps gives 14 IN / 42 OUT vs 15 / 44 at 30 fps.
- On long runs the fanless M1 gets hot and slows down; in an earlier 40-minute run the speed fell to 3–4 FPS per camera.

## Known failure cases

Timestamps are video time in each clip. "Fixed" means the config or code was changed and the case was checked again.

| Clip | Time | What happens | Why | Status |
|---|---|---|---|---|
| counter | 00:46–00:53 | Person `#416` waiting in the queue is not counted | Hidden behind the person in front; no box, or a box cut off above the feet | Open (occlusion) |
| counter | 01:13–01:22 | Same person, now `#559`, not counted | Same occlusion; she also got a new ID | Open (occlusion, ID switch) |
| counter | 02:10–02:18 | One person gets three boxes at the same time: `#708` (whole body), `#720` (upper body), `#722` (legs); later also `#746` | YOLO detects body parts as extra people; the boxes overlap too little to be merged | Open. Queue shows 6 instead of 4 at 02:10 (see queue accuracy) |
| counter | 02:25–02:32, 03:23–03:28 | Staff zone shows 0 while the server is there | Server is cut off by the bottom of the picture and half hidden by the table; YOLO misses her | Open. No alert (shorter than 10 s), but these seconds are counted in `empty_counter_seconds` |
| counter | 03:40 | Staff zone shows 2 people (`#1209`) | A seated person behind the coffee urn gets a box cut off by the urn, so the foot point lands in the staff zone | Fixed: staff zone top edge moved down to y = 800 |
| counter | whole clip | Customer being served was not counted in the queue | Legs cut off by the bottom of the picture, so the foot point sits at the very bottom edge, just below the zone | Fixed: queue zone reaches the bottom edge |
| counter_morning | 00:00–00:13, 01:22–01:28 | Staff zone shows 0 while the server is there | Server is bent over behind the counter; YOLO misses the pose | Open. Gave a false empty-counter alert with an earlier queue zone |
| counter_morning | whole clip | People sitting at the café tables were counted in the queue | Queue zone top edge touched the tables | Fixed: top edge moved down 60 px |
| counter_morning | 00:45 | Staff member (pink top) walking through the queue zone is counted as a customer | No staff / customer distinction | Open |
| entrance | 00:48–00:49, 01:01–01:04, 01:16–01:21 | 16 of 59 OUT missed (most in these groups) | Groups leave together and hide each other | Open (occlusion) |
| entrance | first line position | People counted OUT 23 of 59 | Line too close to the door: people disappear through it before they are clearly on the other side | Fixed: line moved further from the door |
| entrance | 03:33–03:34 | `#920` counted OUT, then IN 1.1 s later | Foot point jumps back over the line in a group; 1.1 s is longer than `min_seconds` | Open |
| entrance | 00:04–00:12 (old clip) | Same person counted OUT, IN, OUT, IN | Legs hidden by others, so the box gets shorter and the foot point jumps over the line | Fixed: person must stay on the new side for `min_seconds` (0.15 s) |
| entrance | live run, 3 cameras | `#481` counted OUT, IN, OUT within 11 s | At 3–4 fps (laptop under load) the foot point moves in big steps | Partly fixed: `min_seconds` instead of frames, so the rule means the same at any fps |

## Scaling to 50 cameras

This is a plan, not something built or measured here.

**The load.** The M1 laptop handles about 38 frames per second in total. 50 cameras at full 30 fps would need 1,500. That is about 40 times more, so the setup has to change.

**1. Fewer frames per camera.** Counting people does not need 30 fps. On the entrance clip the door count is almost the same at 10 fps (14 IN / 42 OUT) and 5 fps (13 / 39) as at 30 fps (15 / 44). With 5–10 fps per camera, 50 cameras need 250–500 frames per second.

**2. Smaller frames.** IP cameras usually send a second, low-resolution stream (for example 640×360). YOLO resizes every frame to 640 px anyway, so decoding 1080p is wasted work. Using that stream makes decoding several times cheaper.

**3. One model for many cameras.** Today every camera loads its own copy of the model and sends one frame at a time. Instead: camera threads only read and decode frames, and put them in a queue. One inference worker takes a batch (for example one frame from each of 16 cameras) and runs the model on all of them at once. A GPU is much more efficient on batches. Tracking, line counting, zones and alerts stay per camera, as they are now, so the logic in `app/` does not change.

**4. A GPU server.** An NVIDIA GPU with the model exported to TensorRT in FP16. Ultralytics reports about 1.5 ms per image for YOLO11n on an NVIDIA T4 with TensorRT FP16 (over 600 frames per second, before batching). So one T4-class GPU should carry 50 cameras at 5–10 fps, and a second server gives headroom and failover. Decoding also moves to the GPU's video decoder (NVDEC), so the CPU is not the bottleneck.

**5. Outputs and monitoring.** 50 CSV files and one JSON file do not scale for people to read. Minute rows and alerts go to one database (for example PostgreSQL), and alerts are also sent to a message channel. A dashboard shows each camera's status (connected, FPS, last frame time), so a dead camera is noticed in minutes. The reconnect loop that exists today stays.

**6. Per-camera setup.** Each new camera needs its line and zones drawn once (`tools/draw_zones.py`) and checked with `tools/show_config.py`. With 50 cameras this is the slowest part of a rollout. A small web page for drawing zones would help.

## Privacy

- No face recognition and no attempt to identify anyone. The system only detects and tracks anonymous person boxes.
- Faces are blurred in every published output frame, GIF or video.
