"""Compare hand-counted queue lengths with the system's per-second values.

Usage:
    python tools/evaluate_queue.py labels/counter_queue_hand.csv outputs/counter_seconds.csv

The second file comes from tools/track_preview.py. Prints every labelled
second and the mean absolute error (MAE).
"""
import csv
import sys


def main():
    labels_path, system_path = sys.argv[1], sys.argv[2]
    with open(system_path) as f:
        system = {int(row["second"]): int(row["queue"]) for row in csv.DictReader(f)}
    with open(labels_path) as f:
        labels = list(csv.DictReader(f))

    errors = []
    print("time   hand  system  error")
    for row in labels:
        second, hand = int(row["second"]), int(row["queue"])
        found = system[second]
        errors.append(abs(found - hand))
        print(f"{second // 60:02d}:{second % 60:02d}  {hand:4d}  {found:6d}  {found - hand:+5d}  {row['note']}")

    exact = sum(1 for e in errors if e == 0)
    print(f"\n{len(errors)} labels, MAE = {sum(errors) / len(errors):.2f} people, "
          f"exact = {exact}/{len(errors)}, max error = {max(errors)}")


if __name__ == "__main__":
    main()
