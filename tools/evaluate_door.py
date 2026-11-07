"""Compare the system's door crossings with reference labels.

Usage:
    python tools/evaluate_door.py labels/meva_reference_entrance.csv outputs/entrance_crossings.csv

A label (start_s, end_s, direction) is found if the system has an unused
crossing in the same direction between start_s - 2 s and end_s + 2 s.
System crossings that match no label are false counts.
"""
import csv
import sys

MARGIN = 2  # seconds of slack around each labelled event


def main():
    labels_path, system_path = sys.argv[1], sys.argv[2]
    with open(labels_path) as f:
        labels = sorted(csv.DictReader(f), key=lambda row: float(row["start_s"]))
    with open(system_path) as f:
        crossings = list(csv.DictReader(f))
    used = set()  # indexes of system crossings already matched

    for direction in ("in", "out"):
        found, missed = 0, []
        for label in labels:
            if label["direction"] != direction:
                continue
            start, end = float(label["start_s"]) - MARGIN, float(label["end_s"]) + MARGIN
            match = next((i for i, c in enumerate(crossings) if i not in used
                          and c["direction"] == direction and start <= float(c["second"]) <= end), None)
            if match is None:
                missed.append(label["start_s"])
            else:
                used.add(match)
                found += 1
        system_total = sum(1 for c in crossings if c["direction"] == direction)
        false = [c["second"] for i, c in enumerate(crossings) if i not in used and c["direction"] == direction]
        print(f"{direction.upper()}: labels {found + len(missed)}, system {system_total}, "
              f"found {found}, missed {len(missed)}, false {len(false)}")
        print(f"  missed at (s): {', '.join(missed) or '-'}")
        print(f"  false at (s):  {', '.join(false) or '-'}")


if __name__ == "__main__":
    main()
