"""Counts people crossing the door line, separately IN and OUT."""
import math


class LineCounter:
    """Counts a crossing when a person's foot point moves from one side of the line to the other.

    Rules against double counting:
    - Dead band: within band_px of the line a person has no side yet, so
      someone standing on the line and wobbling never flips side.
    - A side change only counts if the foot is beside the line segment (not past its ends).
    - The new side must hold for min_frames frames, so a box that jumps for a
      moment (e.g. legs hidden behind someone) does not count.
    - The same person cannot be counted in the same direction twice in a row.
    """

    def __init__(self, line_config):
        (self.ax, self.ay), (self.bx, self.by) = line_config["points"]
        self.length = math.hypot(self.bx - self.ax, self.by - self.ay)
        self.band = line_config["band_px"]
        self.min_frames = line_config["min_frames"]
        # +1 or -1: which sign of the distance means "inside"
        self.inside_sign = 1 if self.signed_distance(line_config["inside_point"]) > 0 else -1

        self.side = {}            # track id -> last clear side: +1 inside, -1 outside
        self.frames_on_new_side = {}  # track id -> frames seen on the other side so far
        self.last_direction = {}  # track id -> "in" or "out", the last time it was counted
        self.count_in = 0
        self.count_out = 0

    def signed_distance(self, point):
        """Distance in pixels from the line; the sign tells which side the point is on."""
        px, py = point
        cross = (self.bx - self.ax) * (py - self.ay) - (self.by - self.ay) * (px - self.ax)
        return cross / self.length

    def is_beside_segment(self, point):
        """True if the point is between the two ends of the line (not past them)."""
        px, py = point
        t = ((px - self.ax) * (self.bx - self.ax) + (py - self.ay) * (self.by - self.ay)) / self.length ** 2
        return 0 <= t <= 1

    def update(self, people):
        """Check this frame's people; return a list of new crossings like [(7, "in")]."""
        crossings = []
        for person in people:
            foot = person["foot"]
            distance = self.signed_distance(foot) * self.inside_sign  # > 0 means inside
            if abs(distance) < self.band or not self.is_beside_segment(foot):
                continue  # on the line or past its ends: no decision

            track_id = person["id"]
            new_side = 1 if distance > 0 else -1
            old_side = self.side.get(track_id)
            if old_side is None:
                self.side[track_id] = new_side  # first time we see this person
                continue
            if new_side == old_side:
                self.frames_on_new_side[track_id] = 0
                continue

            # The person must stay on the new side for a few frames before we believe it
            self.frames_on_new_side[track_id] = self.frames_on_new_side.get(track_id, 0) + 1
            if self.frames_on_new_side[track_id] < self.min_frames:
                continue
            self.frames_on_new_side[track_id] = 0
            self.side[track_id] = new_side

            direction = "in" if new_side == 1 else "out"
            if self.last_direction.get(track_id) == direction:
                continue  # already counted this way, e.g. after a tracking glitch
            self.last_direction[track_id] = direction

            if direction == "in":
                self.count_in += 1
            else:
                self.count_out += 1
            crossings.append((track_id, direction))
        return crossings
