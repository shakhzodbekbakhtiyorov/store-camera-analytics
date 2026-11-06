"""Tests for zone counting and alerts with made-up numbers (no video needed).

Run:  python tests/test_zones_alerts.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.alerts import Alert, CounterAlerts  # noqa: E402
from app.zones import ZoneMonitor  # noqa: E402

# Queue zone: square 0..100. Staff zone: square 200..300.
CAMERA = {"queue_zone": [[0, 0], [100, 0], [100, 100], [0, 100]],
          "staff_zone": [[200, 0], [300, 0], [300, 100], [200, 100]]}


def person(x, y):
    return {"id": 0, "foot": (x, y)}


def run_alert(alert, values, threshold=1):
    """Feed one value per second; return all events."""
    events = []
    for second, value in enumerate(values):
        event = alert.update(second, value >= threshold, value)
        if event:
            events.append(event)
    return events


def test_zone_value_is_median_of_the_second():
    monitor = ZoneMonitor(CAMERA)
    # Second 0: 2 people in the queue in most frames, detector misses one in a single frame
    for frame, people in enumerate([[person(10, 10), person(50, 50)]] * 2 + [[person(10, 10)]]):
        monitor.update(people, video_time=frame / 3)
    second, queue, staff = monitor.update([], video_time=1.0)  # first frame of second 1 closes second 0
    assert (second, queue, staff) == (0, 2, 0)


def test_staff_zone_counted_separately():
    monitor = ZoneMonitor(CAMERA)
    monitor.update([person(10, 10), person(250, 50)], video_time=0.0)
    assert monitor.update([], video_time=1.0) == (0, 1, 1)


def test_alert_starts_after_min_seconds():
    events = run_alert(Alert("queue", min_seconds=3, clear_seconds=2), [1, 1, 1])
    assert events == [{"alert": "queue", "event": "start", "start": 0, "peak": 1}]


def test_short_run_does_not_start_alert():
    events = run_alert(Alert("queue", min_seconds=3, clear_seconds=2), [1, 1, 0, 1, 1, 0])
    assert events == []


def test_short_gap_does_not_flicker():
    # Condition drops for 1 second in the middle: the alert must stay open (starts once, ends once)
    events = run_alert(Alert("queue", min_seconds=2, clear_seconds=2), [1, 1, 1, 0, 1, 1, 0, 0])
    assert [e["event"] for e in events] == ["start", "end"]
    assert events[1]["start"] == 0 and events[1]["end"] == 6


def test_peak_is_largest_value():
    events = run_alert(Alert("queue", min_seconds=2, clear_seconds=1), [3, 5, 4, 0], threshold=3)
    assert events[-1] == {"alert": "queue", "event": "end", "start": 0, "end": 3, "peak": 5}


def test_empty_counter_needs_someone_waiting():
    alerts = CounterAlerts({"queue_min_people": 3, "queue_min_seconds": 2,
                            "empty_counter_seconds": 2, "clear_seconds": 1})
    events = []
    for second in range(5):  # nobody at the counter and nobody waiting: no alert
        events += alerts.update(second, queue_people=0, staff_people=0)
    for second in range(5, 8):  # nobody at the counter, 1 person waiting: alert
        events += alerts.update(second, queue_people=1, staff_people=0)
    assert [(e["alert"], e["event"], e["start"]) for e in events] == [("empty_counter", "start", 5)]


def test_open_alert_closed_at_end_of_video():
    alerts = CounterAlerts({"queue_min_people": 2, "queue_min_seconds": 1,
                            "empty_counter_seconds": 99, "clear_seconds": 1})
    alerts.update(0, queue_people=2, staff_people=1)
    assert alerts.finish(second=1) == [{"alert": "queue", "event": "end", "start": 0, "end": 1, "peak": 2}]


if __name__ == "__main__":
    tests = [f for name, f in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print(f"ok  {test.__name__}")
    print(f"{len(tests)} tests passed")
