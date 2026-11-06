"""Click on a video frame to get coordinates for config.yaml.

Usage:
    python tools/draw_zones.py videos/clip.avi [--second 30]

Controls:
    left click  add a point
    u           undo the last point
    n           finish the current shape and print it, start a new one
    q / Esc     quit (prints the current shape if it has points)

The printed points are in original video pixels, ready to paste into the config.
"""
import argparse

import cv2

MAX_WINDOW_WIDTH = 1280  # big frames are shown smaller so they fit on screen


def read_frame(path, second):
    cap = cv2.VideoCapture(path)
    cap.set(cv2.CAP_PROP_POS_MSEC, second * 1000)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise SystemExit(f"Could not read a frame from {path} at {second}s")
    return frame


def print_shape(points):
    print("[" + ", ".join(f"[{x}, {y}]" for x, y in points) + "]")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("video")
    parser.add_argument("--second", type=float, default=0)
    args = parser.parse_args()

    frame = read_frame(args.video, args.second)
    scale = min(1.0, MAX_WINDOW_WIDTH / frame.shape[1])
    shown = cv2.resize(frame, None, fx=scale, fy=scale)
    points = []  # in original pixels

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            points.append((round(x / scale), round(y / scale)))

    cv2.namedWindow("draw_zones")
    cv2.setMouseCallback("draw_zones", on_mouse)
    print("Click points. n = finish shape, u = undo, q = quit")

    while True:
        canvas = shown.copy()
        screen_points = [(round(x * scale), round(y * scale)) for x, y in points]
        for p in screen_points:
            cv2.circle(canvas, p, 4, (0, 0, 255), -1)
        for a, b in zip(screen_points, screen_points[1:]):
            cv2.line(canvas, a, b, (0, 255, 255), 2)
        cv2.imshow("draw_zones", canvas)

        key = cv2.waitKey(30) & 0xFF
        if key == ord("u") and points:
            points.pop()
        elif key == ord("n") and points:
            print_shape(points)
            points.clear()
        elif key in (ord("q"), 27):
            if points:
                print_shape(points)
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
