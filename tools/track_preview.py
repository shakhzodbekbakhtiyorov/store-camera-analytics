"""Run detection + tracking on one camera and save a video with boxes and IDs.

Usage:
    python tools/track_preview.py entrance [--seconds 60]

Saves outputs/track_<camera>.mp4 and prints the processing speed (FPS).
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
from app.zones import ZoneMonitor  # noqa: E402

GREEN, RED, YELLOW, ORANGE, CYAN = (0, 255, 0), (0, 0, 255), (0, 255, 255), (0, 140, 255), (255, 255, 0)


def mmss(seconds):
    tenths = round(seconds * 10)  # round first, so 299.99 s shows as 05:00.0, not 04:60.0
    return f"{tenths // 600:02d}:{tenths % 600 / 10:04.1f}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("camera", help="camera name from config.yaml")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--seconds", type=float, default=60)
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

        if line_counter:
            for track_id, direction in line_counter.update(people):
                print(f"{mmss(video_time)}  #{track_id} {direction.upper()}")
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

        for person in people:
            x1, y1, x2, y2 = map(int, person["box"])
            cv2.rectangle(frame, (x1, y1), (x2, y2), GREEN, 2)
            cv2.putText(frame, f"#{person['id']}", (x1, y1 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, GREEN, 2)
            cv2.circle(frame, tuple(map(int, person["foot"])), 6, RED, -1)
        writer.write(frame)

    elapsed = time.time() - start
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
