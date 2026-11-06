"""Counts people inside the queue and staff zones, one value per second."""
from statistics import median_low

import cv2
import numpy as np


def is_inside(polygon, point):
    """True if the point is inside the polygon or on its edge."""
    return cv2.pointPolygonTest(polygon, point, False) >= 0


def count_in_zone(polygon, people):
    """How many people have their foot point inside the polygon."""
    return sum(1 for p in people if is_inside(polygon, p["foot"]))


class ZoneMonitor:
    """Collects per-frame zone counts and gives one value per second.

    The value for a second is the median of that second's frames, so a person
    missed by the detector in a few frames does not change the number.
    """

    def __init__(self, camera_config):
        self.queue_zone = np.array(camera_config["queue_zone"], dtype=np.float32)
        self.staff_zone = np.array(camera_config["staff_zone"], dtype=np.float32)
        self.current_second = 0
        self.queue_counts = []  # one number per frame in the current second
        self.staff_counts = []

    def update(self, people, video_time):
        """Call every frame. When a second is complete, return (second, queue, staff); else None."""
        second = int(video_time)
        finished = None
        if second > self.current_second and self.queue_counts:
            finished = (self.current_second, median_low(self.queue_counts), median_low(self.staff_counts))
            self.queue_counts, self.staff_counts = [], []
        self.current_second = second

        self.queue_counts.append(count_in_zone(self.queue_zone, people))
        self.staff_counts.append(count_in_zone(self.staff_zone, people))
        return finished
