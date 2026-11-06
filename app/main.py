"""Runs every camera from the config at the same time.

Usage:
    python -m app.main [--config config.yaml] [--duration 300]

Stop with Ctrl+C, or let --duration (seconds) stop it.
Outputs: outputs/<camera>_minutes.csv and outputs/alerts.jsonl
"""
import argparse
import logging
import os
import threading
import time

import yaml

from app.camera import CameraWorker
from app.report import AlertLog

STATUS_EVERY_SECONDS = 10


def print_status(workers):
    parts = []
    for w in workers:
        text = f"{w.name}: {'ok' if w.status['connected'] else 'DOWN'} {w.status['fps']:.1f} fps"
        if w.line_counter:
            text += f", in {w.line_counter.count_in} out {w.line_counter.count_out}"
        if w.zones:
            text += f", queue {w.status['queue']} staff {w.status['staff']}"
        parts.append(text)
    total_fps = sum(w.status["fps"] for w in workers)
    logging.info("status | %s | total %.1f fps", " | ".join(parts), total_fps)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--duration", type=float, default=None, help="stop after this many seconds")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    with open(args.config) as f:
        config = yaml.safe_load(f)
    os.makedirs(config["output_dir"], exist_ok=True)

    stop_event = threading.Event()
    alert_log = AlertLog(os.path.join(config["output_dir"], "alerts.jsonl"))
    workers = [CameraWorker(camera, config, alert_log, stop_event) for camera in config["cameras"]]
    for worker in workers:
        worker.start()

    start = time.time()
    try:
        while not stop_event.is_set():
            stop_event.wait(STATUS_EVERY_SECONDS)
            print_status(workers)
            if args.duration and time.time() - start >= args.duration:
                stop_event.set()
    except KeyboardInterrupt:
        stop_event.set()

    logging.info("stopping...")
    for worker in workers:
        worker.join()
    alert_log.close()


if __name__ == "__main__":
    main()
