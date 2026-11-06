"""Output files: one per-minute CSV per camera, and one JSON-lines file for all alert events."""
import csv
import json
import threading
import time
from statistics import mean


def to_time_text(epoch_seconds):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(epoch_seconds))


class MinuteReport:
    """Collects one camera's numbers and writes one CSV row per minute.

    Columns that a camera does not have (no door line, or no zones) are left empty.
    """

    HEADER = ["minute", "in", "out", "avg_queue", "max_queue", "empty_counter_seconds"]

    def __init__(self, path, has_line, has_zones):
        self.has_line = has_line
        self.has_zones = has_zones
        self.file = open(path, "a", newline="")
        self.writer = csv.writer(self.file)
        if self.file.tell() == 0:  # new file: write the header once
            self.writer.writerow(self.HEADER)
        self.minute = None
        self.reset()

    def reset(self):
        self.count_in = 0
        self.count_out = 0
        self.queue_values = []  # one value per second
        self.empty_counter_seconds = 0

    def update(self, now, crossings, zone_second):
        """Call every frame with this frame's crossings and (if a second just finished) its zone values."""
        if zone_second:  # added first: it belongs to the second that just ended
            _, queue, staff = zone_second
            self.queue_values.append(queue)
            if staff == 0:
                self.empty_counter_seconds += 1

        minute = int(now // 60)
        if self.minute is not None and minute != self.minute:
            self.write_row()
        self.minute = minute

        for _, direction in crossings:
            if direction == "in":
                self.count_in += 1
            else:
                self.count_out += 1

    def write_row(self):
        line = [self.count_in, self.count_out] if self.has_line else ["", ""]
        if self.has_zones and self.queue_values:
            zones = [round(mean(self.queue_values), 2), max(self.queue_values), self.empty_counter_seconds]
        else:
            zones = ["", "", ""]
        self.writer.writerow([to_time_text(self.minute * 60)[:-3]] + line + zones)
        self.file.flush()  # so the file is up to date even if the service is killed
        self.reset()

    def close(self):
        if self.minute is not None:
            self.write_row()  # the last, unfinished minute
        self.file.close()


class AlertLog:
    """Appends alert events as JSON lines. Shared by all cameras, so writes are locked."""

    def __init__(self, path):
        self.file = open(path, "a")
        self.lock = threading.Lock()

    def write(self, camera_name, event):
        record = {"camera": camera_name, **event}
        for key in ("start", "end"):
            if key in record:
                record[key] = to_time_text(record[key])
        with self.lock:
            self.file.write(json.dumps(record) + "\n")
            self.file.flush()

    def close(self):
        self.file.close()
