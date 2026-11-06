"""Person detection (YOLO) + tracking (ByteTrack) for one camera."""
from ultralytics import YOLO

PERSON_CLASS = 0  # in the COCO dataset YOLO was trained on, class 0 is "person"


class PersonTracker:
    """Finds people in each frame and keeps the same ID on the same person.

    Make one PersonTracker per camera: the tracker remembers the previous
    frames, so two cameras must not share it.
    """

    def __init__(self, model_config):
        self.config = model_config
        self.model = YOLO(model_config["weights"])

    def update(self, frame):
        """Return a list of people: {"id", "box": (x1, y1, x2, y2), "foot": (x, y)}."""
        result = self.model.track(
            frame,
            persist=True,              # keep tracks from the previous frame
            classes=[PERSON_CLASS],    # ignore everything except people
            tracker=self.config["tracker"],
            imgsz=self.config["imgsz"],
            conf=self.config["conf"],
            device=self.config["device"],
            verbose=False,
        )[0]

        if result.boxes.id is None:  # no tracked people in this frame
            return []

        people = []
        for box, track_id in zip(result.boxes.xyxy.tolist(), result.boxes.id.int().tolist()):
            x1, y1, x2, y2 = box
            foot = ((x1 + x2) / 2, y2)  # bottom-centre of the box = where the person stands
            people.append({"id": track_id, "box": (x1, y1, x2, y2), "foot": foot})
        return people
