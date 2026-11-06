"""Draw the line and zones from config.yaml on one frame of each camera, to check them.

Usage:
    python tools/show_config.py [--config config.yaml] [--second 30]

Saves one image per camera to outputs/config_<camera>.jpg
"""
import argparse
import os

import cv2
import numpy as np
import yaml

YELLOW, ORANGE, CYAN = (0, 255, 255), (0, 140, 255), (255, 255, 0)


def draw_polygon(frame, points, color, label):
    pts = np.array(points, dtype=np.int32)
    cv2.polylines(frame, [pts], isClosed=True, color=color, thickness=3)
    cv2.putText(frame, label, tuple(pts[0]), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--second", type=float, default=30)
    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f)
    os.makedirs(config["output_dir"], exist_ok=True)

    for camera in config["cameras"]:
        cap = cv2.VideoCapture(camera["source"])
        cap.set(cv2.CAP_PROP_POS_MSEC, args.second * 1000)
        ok, frame = cap.read()
        cap.release()
        if not ok:
            print(f"{camera['name']}: could not read {camera['source']}")
            continue

        if "door_line" in camera:
            line = camera["door_line"]
            a, b = (tuple(p) for p in line["points"])
            cv2.line(frame, a, b, YELLOW, 3)
            cv2.circle(frame, tuple(line["inside_point"]), 10, YELLOW, -1)
            cv2.putText(frame, "IN side", tuple(line["inside_point"]),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, YELLOW, 3)
        if "queue_zone" in camera:
            draw_polygon(frame, camera["queue_zone"], ORANGE, "queue")
        if "staff_zone" in camera:
            draw_polygon(frame, camera["staff_zone"], CYAN, "staff")

        path = os.path.join(config["output_dir"], f"config_{camera['name']}.jpg")
        cv2.imwrite(path, frame)
        print(f"{camera['name']}: saved {path}")


if __name__ == "__main__":
    main()
