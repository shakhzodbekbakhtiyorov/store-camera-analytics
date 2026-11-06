"""One camera = one thread: read frames, track people, count, check zones, write outputs."""
import logging
import os
import threading
import time

import cv2

from app.alerts import CounterAlerts
from app.line_counter import LineCounter
from app.report import MinuteReport
from app.tracking import PersonTracker
from app.zones import ZoneMonitor

log = logging.getLogger(__name__)


class CameraWorker(threading.Thread):
    """Processes one video source until stop_event is set.

    If the source fails to open, drops, or ends, the worker waits
    reconnect_seconds and opens it again. Errors stay inside this thread,
    so the other cameras keep running.
    """

    def __init__(self, camera_config, config, alert_log, stop_event):
        super().__init__(name=camera_config["name"], daemon=True)
        self.camera = camera_config
        self.source = camera_config["source"]
        self.reconnect_seconds = config["reconnect_seconds"]
        self.alert_log = alert_log
        self.stop_event = stop_event

        self.tracker = PersonTracker(config["model"])  # own model per camera: tracker state is per model
        self.line_counter = LineCounter(camera_config["door_line"]) if "door_line" in camera_config else None
        self.zones = ZoneMonitor(camera_config) if "queue_zone" in camera_config else None
        self.alerts = CounterAlerts(camera_config["alerts"]) if self.zones else None
        csv_path = os.path.join(config["output_dir"], f"{self.name}_minutes.csv")
        self.report = MinuteReport(csv_path, has_line=bool(self.line_counter), has_zones=bool(self.zones))

        self.status = {"connected": False, "fps": 0.0, "queue": None, "staff": None}  # read by main.py

    def run(self):
        while not self.stop_event.is_set():
            try:
                self.process_stream()
            except Exception as error:  # any failure: log it, wait, reconnect
                log.warning("%s: %s", self.name, error)
            self.status["connected"] = False
            if not self.stop_event.is_set():
                log.info("%s: reconnecting in %s s", self.name, self.reconnect_seconds)
                self.stop_event.wait(self.reconnect_seconds)

        if self.alerts:  # close alerts that are still open when the service stops
            for event in self.alerts.finish(int(time.time())):
                self.alert_log.write(self.name, event)
        self.report.close()

    def process_stream(self):
        cap = cv2.VideoCapture(self.source)
        if not cap.isOpened():
            raise ConnectionError(f"cannot open {self.source}")
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        is_file = os.path.isfile(self.source)
        log.info("%s: connected (%.0f fps, %s)", self.name, fps, "file" if is_file else "stream")
        self.status["connected"] = True

        start = time.time()
        frame_index = 0           # position in the video
        processed, fps_timer = 0, time.time()
        try:
            while not self.stop_event.is_set():
                if is_file:
                    # Play the file like a live camera: skip frames we are already late for,
                    # and wait if we are early. A real stream does this by itself.
                    due = int((time.time() - start) * fps)
                    while frame_index < due and cap.grab():
                        frame_index += 1
                    wait = start + frame_index / fps - time.time()
                    if wait > 0:
                        time.sleep(wait)

                ok, frame = cap.read()
                if not ok:
                    raise ConnectionError("stream ended or dropped")
                frame_index += 1
                self.process_frame(frame, time.time())

                processed += 1
                if time.time() - fps_timer >= 5:  # update the measured speed every 5 s
                    self.status["fps"] = processed / (time.time() - fps_timer)
                    processed, fps_timer = 0, time.time()
        finally:
            cap.release()

    def process_frame(self, frame, now):
        people = self.tracker.update(frame)
        crossings = self.line_counter.update(people, now) if self.line_counter else []
        for track_id, direction in crossings:
            log.info("%s: #%s %s", self.name, track_id, direction.upper())

        zone_second = self.zones.update(people, now) if self.zones else None
        if zone_second:
            _, self.status["queue"], self.status["staff"] = zone_second
            for event in self.alerts.update(*zone_second):
                log.info("%s: alert %s %s", self.name, event["alert"], event["event"])
                self.alert_log.write(self.name, event)

        self.report.update(now, crossings, zone_second)
