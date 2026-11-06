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
from app.tracking import PersonTracker  # noqa: E402

GREEN, RED = (0, 255, 0), (0, 0, 255)


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
    max_frames = int(args.seconds * fps)
    start = time.time()

    for frame_index in range(max_frames):
        ok, frame = cap.read()
        if not ok:
            break
        for person in tracker.update(frame):
            x1, y1, x2, y2 = map(int, person["box"])
            cv2.rectangle(frame, (x1, y1), (x2, y2), GREEN, 2)
            cv2.putText(frame, f"#{person['id']}", (x1, y1 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, GREEN, 2)
            cv2.circle(frame, tuple(map(int, person["foot"])), 6, RED, -1)
        writer.write(frame)

    elapsed = time.time() - start
    cap.release()
    writer.release()
    print(f"{args.camera}: {frame_index + 1} frames in {elapsed:.1f}s "
          f"= {(frame_index + 1) / elapsed:.1f} FPS -> {out_path}")


if __name__ == "__main__":
    main()
