"""Run detection + tracking on one camera and save a video with boxes and IDs.

Usage:
    python tools/track_preview.py entrance [--seconds 60] [--blur]

Saves outputs/track_<camera>.mp4 and prints the processing speed (FPS).
--blur blurs the head of every tracked person, for videos or GIFs you publish.
"""
import argparse
import os
import sys
import time

import cv2
import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.alerts import CounterAlerts  # noqa: E402
from app.line_counter import LineCounter  # noqa: E402
from app.tracking import PersonTracker  # noqa: E402
from app.zones import ZoneMonitor, is_inside  # noqa: E402

GREEN, RED, YELLOW, ORANGE, CYAN = (0, 255, 0), (0, 0, 255), (0, 255, 255), (0, 140, 255), (255, 255, 0)


def mmss(seconds):
    tenths = round(seconds * 10)  # round first, so 299.99 s shows as 05:00.0, not 04:60.0
    return f"{tenths // 600:02d}:{tenths % 600 / 10:04.1f}"


def blur_heads(frame, people):
    """Blur the top third of every person box (where the head is), so nobody can be recognised."""
    for person in people:
        x1, y1, x2, y2 = map(int, person["box"])
        x1, y1 = max(x1, 0), max(y1, 0)
        head_bottom = y1 + max((y2 - y1) // 3, 1)
        if x2 > x1 and head_bottom > y1:
            frame[y1:head_bottom, x1:x2] = cv2.GaussianBlur(frame[y1:head_bottom, x1:x2], (51, 51), 0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("camera", help="camera name from config.yaml")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--seconds", type=float, default=60)
    parser.add_argument("--blur", action="store_true", help="blur heads in the saved video")
    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f)
    camera = next(c for c in config["cameras"] if c["name"] == args.camera)

    cap = cv2.VideoCapture(camera["source"])
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    os.makedirs(config["output_dir"], exist_ok=True)
    out_path = os.path.join(config["output_dir"], f"track_{args.camera}.mp4")
    writer = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))

    tracker = PersonTracker(config["model"])
    line_counter = LineCounter(camera["door_line"]) if "door_line" in camera else None
    zones = ZoneMonitor(camera) if "queue_zone" in camera else None
    alerts = CounterAlerts(camera["alerts"]) if zones else None
    queue_now, staff_now = 0, 0
    if line_counter:  # one line per crossing, to compare with reference labels later
        crossings_file = open(os.path.join(config["output_dir"], f"{args.camera}_crossings.csv"), "w")
        crossings_file.write("second,id,direction\n")
    if zones:  # one line per second, to compare with hand labels later
        seconds_file = open(os.path.join(config["output_dir"], f"{args.camera}_seconds.csv"), "w")
        seconds_file.write("second,queue,staff\n")
    max_frames = int(args.seconds * fps)
    start = time.time()

    for frame_index in range(max_frames):
        ok, frame = cap.read()
        if not ok:
            break
        people = tracker.update(frame)
        video_time = frame_index / fps
        if args.blur:
            blur_heads(frame, people)  # before drawing, so the labels stay sharp

        if line_counter:
            for track_id, direction in line_counter.update(people, video_time):
                print(f"{mmss(video_time)}  #{track_id} {direction.upper()}")
                crossings_file.write(f"{video_time:.2f},{track_id},{direction}\n")
            a, b = (tuple(p) for p in camera["door_line"]["points"])
            cv2.line(frame, a, b, YELLOW, 3)
            cv2.putText(frame, f"IN {line_counter.count_in}  OUT {line_counter.count_out}",
                        (40, 80), cv2.FONT_HERSHEY_SIMPLEX, 2.0, YELLOW, 4)

        if zones:
            finished = zones.update(people, video_time)
            if finished:
                second, queue_now, staff_now = finished
                seconds_file.write(f"{second},{queue_now},{staff_now}\n")
                for event in alerts.update(second, queue_now, staff_now):
                    print(f"{mmss(second)}  {event}")
            cv2.polylines(frame, [zones.queue_zone.astype(int)], True, ORANGE, 3)
            cv2.polylines(frame, [zones.staff_zone.astype(int)], True, CYAN, 3)
            open_alerts = [a.name for a in (alerts.queue_alert, alerts.empty_counter_alert) if a.active]
            cv2.putText(frame, f"queue {queue_now}  staff {staff_now}  alerts: {', '.join(open_alerts) or '-'}",
                        (40, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.6, ORANGE, 4)
            # Who is in the queue zone in this frame (the per-second number is the median of these)
            queue_ids = [f"#{p['id']}" for p in people if is_inside(zones.queue_zone, p["foot"])]
            cv2.putText(frame, f"in queue now: {' '.join(queue_ids) or '-'}",
                        (40, 140), cv2.FONT_HERSHEY_SIMPLEX, 1.2, ORANGE, 3)

        cv2.putText(frame, mmss(video_time), (width - 260, 80), cv2.FONT_HERSHEY_SIMPLEX, 2.0, YELLOW, 4)

        for person in people:
            # Orange = counted in the queue zone, cyan = in the staff zone, green = elsewhere
            color, tag = GREEN, ""
            if zones and is_inside(zones.queue_zone, person["foot"]):
                color, tag = ORANGE, "Q "
            elif zones and is_inside(zones.staff_zone, person["foot"]):
                color, tag = CYAN, "S "
            x1, y1, x2, y2 = map(int, person["box"])
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 4 if tag else 2)
            cv2.putText(frame, f"{tag}#{person['id']}", (x1, y1 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)
            cv2.circle(frame, tuple(map(int, person["foot"])), 6, RED, -1)
        writer.write(frame)

    elapsed = time.time() - start
    if line_counter:
        crossings_file.close()
    if zones:
        for event in alerts.finish(second=int(video_time)):
            print(f"{mmss(video_time)}  {event}")
        seconds_file.close()
    cap.release()
    writer.release()
    print(f"{args.camera}: {frame_index + 1} frames in {elapsed:.1f}s "
          f"= {(frame_index + 1) / elapsed:.1f} FPS -> {out_path}")


if __name__ == "__main__":
    main()
