"""Alerts that start once, end once, and remember their peak value."""


class Alert:
    """One alert type, fed one value per second.

    - Starts when the condition has been true for min_seconds in a row.
      Its start time is the first second of that run.
    - Ends only when the condition has been false for clear_seconds in a row,
      so a short gap does not end it and start it again (no flicker).
    - peak is the largest value seen while the condition was true.
    """

    def __init__(self, name, min_seconds, clear_seconds):
        self.name = name
        self.min_seconds = min_seconds
        self.clear_seconds = clear_seconds
        self.active = False
        self.true_since = None   # first second of the current "condition true" run
        self.false_since = None  # first second of the current "condition false" run (while active)
        self.peak = 0

    def update(self, second, condition, value):
        """Feed one second. Returns an event dict when the alert starts or ends, else None."""
        if condition:
            self.false_since = None
            if self.true_since is None:
                self.true_since = second
                self.peak = 0
            self.peak = max(self.peak, value)
            if not self.active and second - self.true_since + 1 >= self.min_seconds:
                self.active = True
                return {"alert": self.name, "event": "start", "start": self.true_since, "peak": self.peak}
            return None

        if not self.active:
            self.true_since = None  # the run was too short, forget it
            return None
        if self.false_since is None:
            self.false_since = second
        if second - self.false_since + 1 >= self.clear_seconds:
            return self.finish(end=self.false_since)
        return None

    def finish(self, end):
        """End the alert (also used when the video stops while it is still open)."""
        event = {"alert": self.name, "event": "end", "start": self.true_since, "end": end, "peak": self.peak}
        self.active = False
        self.true_since = None
        self.false_since = None
        return event


class CounterAlerts:
    """The two alerts from the case study, driven by the per-second zone counts."""

    def __init__(self, alert_config):
        self.queue_min_people = alert_config["queue_min_people"]
        clear = alert_config["clear_seconds"]
        self.queue_alert = Alert("queue", alert_config["queue_min_seconds"], clear)
        self.empty_counter_alert = Alert("empty_counter", alert_config["empty_counter_seconds"], clear)

    def update(self, second, queue_people, staff_people):
        """Returns the list of alert events for this second (usually empty)."""
        events = [
            # (a) at least N people in the queue; peak = longest queue
            self.queue_alert.update(second, queue_people >= self.queue_min_people, queue_people),
            # (b) nobody at the counter while someone waits; peak = longest queue left waiting
            self.empty_counter_alert.update(second, staff_people == 0 and queue_people >= 1, queue_people),
        ]
        return [e for e in events if e]

    def finish(self, second):
        """Close alerts that are still open at the end of the video."""
        return [a.finish(end=second) for a in (self.queue_alert, self.empty_counter_alert) if a.active]
