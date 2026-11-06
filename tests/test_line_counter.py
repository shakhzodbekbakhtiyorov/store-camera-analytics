"""Tests for the door counter with made-up foot positions (no video needed).

Run:  python tests/test_line_counter.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.line_counter import LineCounter  # noqa: E402

# A horizontal line from x=0 to x=100 at y=50. Inside is below it (bigger y).
LINE = {"points": [[0, 50], [100, 50]], "inside_point": [50, 100], "band_px": 10, "min_seconds": 0}


FPS = 10


def walk(counter, track_id, positions, start_frame=0):
    """Feed one person's foot positions frame by frame, at FPS frames per second."""
    for i, foot in enumerate(positions, start=start_frame):
        counter.update([{"id": track_id, "foot": foot}], now=i / FPS)


def test_walk_in():
    counter = LineCounter(LINE)
    walk(counter, 1, [(50, 20), (50, 40), (50, 60), (50, 80)])
    assert (counter.count_in, counter.count_out) == (1, 0)


def test_walk_out():
    counter = LineCounter(LINE)
    walk(counter, 1, [(50, 80), (50, 60), (50, 40), (50, 20)])
    assert (counter.count_in, counter.count_out) == (0, 1)


def test_standing_on_line_with_jitter():
    counter = LineCounter(LINE)
    walk(counter, 1, [(50, 30), (50, 45), (50, 55), (50, 44), (50, 56), (50, 48), (50, 30)])
    assert (counter.count_in, counter.count_out) == (0, 0)


def test_turn_back_counts_in_then_out():
    counter = LineCounter(LINE)
    walk(counter, 1, [(50, 20), (50, 80), (50, 20)])
    assert (counter.count_in, counter.count_out) == (1, 1)


def test_walk_along_line():
    counter = LineCounter(LINE)
    walk(counter, 1, [(x, 52) for x in range(0, 101, 10)])
    assert (counter.count_in, counter.count_out) == (0, 0)


def test_pass_beyond_line_end():
    counter = LineCounter(LINE)
    walk(counter, 1, [(150, 20), (150, 80)])  # x=150 is past the end of the line
    assert (counter.count_in, counter.count_out) == (0, 0)


def test_same_direction_not_counted_twice():
    counter = LineCounter(LINE)
    # Inside, then jumps outside without being seen crossing (tracking glitch), then inside again
    walk(counter, 1, [(50, 20), (50, 80)])
    counter.side[1] = -1  # pretend the tracker put this person outside again
    walk(counter, 1, [(50, 80)])
    assert (counter.count_in, counter.count_out) == (1, 0)


def test_short_jump_across_line_ignored():
    counter = LineCounter({**LINE, "min_seconds": 0.2})
    # Box bottom jumps inside for 2 frames = 0.1 s (legs hidden), then back outside
    walk(counter, 1, [(50, 20), (50, 80), (50, 80), (50, 20), (50, 20)])
    assert (counter.count_in, counter.count_out) == (0, 0)


def test_real_crossing_with_min_seconds():
    counter = LineCounter({**LINE, "min_seconds": 0.2})
    walk(counter, 1, [(50, 20), (50, 80), (50, 85), (50, 90), (50, 95)])  # inside from 0.1 s to 0.4 s
    assert (counter.count_in, counter.count_out) == (1, 0)


def test_min_seconds_same_at_low_fps():
    # At 2 fps a single frame on the other side already lasts 0.5 s: the rule is about time, not frames
    counter = LineCounter({**LINE, "min_seconds": 0.4})
    for i, foot in enumerate([(50, 20), (50, 80), (50, 80)]):
        counter.update([{"id": 1, "foot": foot}], now=i / 2)
    assert (counter.count_in, counter.count_out) == (1, 0)


def test_two_people_counted_separately():
    counter = LineCounter(LINE)
    walk(counter, 1, [(30, 20), (30, 80)])
    walk(counter, 2, [(70, 20), (70, 80)])
    assert (counter.count_in, counter.count_out) == (2, 0)


if __name__ == "__main__":
    tests = [f for name, f in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print(f"ok  {test.__name__}")
    print(f"{len(tests)} tests passed")
