# Store Camera Analytics

Store analytics case study (ML Engineer, computer vision): person detection and tracking, door IN/OUT counting, queue and counter zones with alerts, on several video streams at once.

All footage is public and licensed for download, processing and display. No private or company footage is used.

## Video sources and licences

Videos are **not stored in this repository**. They are downloaded by script from the source URLs below.

### Pexels clips

Licence: [Pexels License](https://www.pexels.com/license/). Free to download, edit and use; attribution is not required (given here anyway).

| File | Source URL | Author | Resolution / FPS | Timestamps used |
|---|---|---|---|---|
| `door_store_sliding_doors_6641527.mp4` | https://www.pexels.com/video/people-going-inside-a-store-with-automatic-sliding-doors-6641527/ | [Casey Whalen](https://www.pexels.com/@casey-whalen-20197262/) | 1920×1080, 30 fps | 00:00–00:19 (full clip) |
| `candidate_casey_whalen_6641461.mp4` | https://www.pexels.com/video/food-people-exit-market-6641461/ | [Casey Whalen](https://www.pexels.com/@casey-whalen-20197262/) | 1920×1080, 30 fps | 00:00–00:12 (full clip) |
| `candidate_casey_whalen_6641343.mp4` | https://www.pexels.com/video/a-person-entering-a-commercial-establishment-6641343/ | [Casey Whalen](https://www.pexels.com/@casey-whalen-20197262/) | 1920×1080, 30 fps | 00:00–00:18 (full clip) |
| `candidate_casey_whalen_6641422.mp4` | https://www.pexels.com/video/food-people-exit-market-6641422/ | [Casey Whalen](https://www.pexels.com/@casey-whalen-20197262/) | 1920×1080, 30 fps | 00:00–00:10 (full clip) |

Direct download links (1080p):

```
https://videos.pexels.com/video-files/6641527/6641527-hd_1920_1080_30fps.mp4
https://videos.pexels.com/video-files/6641461/6641461-hd_1920_1080_30fps.mp4
https://videos.pexels.com/video-files/6641343/6641343-hd_1920_1080_30fps.mp4
https://videos.pexels.com/video-files/6641422/6641422-hd_1920_1080_30fps.mp4
```

### CAVIAR dataset (shopping centre, Lisbon)

- **Source:** CAVIAR Test Case Scenarios, second set ("Clips from Shopping Center in Portugal"), frontal view of a shop entrance: https://homepages.inf.ed.ac.uk/rbf/CAVIARDATA1/
- **Author:** EC Funded CAVIAR project/IST 2001 37540 (https://homepages.inf.ed.ac.uk/rbf/CAVIAR/), University of Edinburgh.
- **Licence:** Creative Commons Attribution-ShareAlike (CC BY-SA). The source page states "Usability is Creative Commons BY-SA" without a version number; for reference see https://creativecommons.org/licenses/by-sa/4.0/.
- **Required acknowledgement:** *Data from the EC Funded CAVIAR project/IST 2001 37540, found at URL: http://homepages.inf.ed.ac.uk/rbf/CAVIAR/*
- **Share-alike:** output frames, GIFs or videos made from these clips are shared under CC BY-SA as well.

All clips: 384×288, 25 fps, MPEG-1. The container's duration field is unreliable for these files, so lengths below are computed from frame counts.

| File | Source URL | Frames | Timestamps used |
|---|---|---|---|
| `caviar_EnterExitCrossingPaths1front.mpg` | https://homepages.inf.ed.ac.uk/rbf/CAVIARDATA2/EnterExitCrossingPaths1front/EnterExitCrossingPaths1front.mpg | 383 | 00:00–00:15 (full clip) |
| `caviar_OneShopOneWait1front.mpg` | https://homepages.inf.ed.ac.uk/rbf/CAVIARDATA2/OneShopOneWait1front/OneShopOneWait1front.mpg | 1377 | 00:00–00:55 (full clip) |
| `caviar_OneShopOneWait2front.mpg` | https://homepages.inf.ed.ac.uk/rbf/CAVIARDATA2/OneShopOneWait2front/OneShopOneWait2front.mpg | 1462 | 00:00–00:58 (full clip) |
| `caviar_OneStopMoveEnter1front.mpg` | https://homepages.inf.ed.ac.uk/rbf/CAVIARDATA2/OneStopMoveEnter1front/OneStopMoveEnter1front.mpg | 1590 | 00:00–01:03 (full clip) |
| `caviar_OneStopMoveEnter2front.mpg` | https://homepages.inf.ed.ac.uk/rbf/CAVIARDATA2/OneStopMoveEnter2front/OneStopMoveEnter2front.mpg | 2237 | 00:00–01:29 (full clip) |
| `caviar_TwoEnterShop1front.mpg` | https://homepages.inf.ed.ac.uk/rbf/CAVIARDATA2/TwoEnterShop1front/TwoEnterShop1front.mpg | 1645 | 00:00–01:05 (full clip) |
| `caviar_TwoEnterShop2front.mpg` | https://homepages.inf.ed.ac.uk/rbf/CAVIARDATA2/TwoEnterShop2front/TwoEnterShop2front.mpg | 1605 | 00:00–01:04 (full clip) |
| `caviar_TwoEnterShop3front.mpg` | https://homepages.inf.ed.ac.uk/rbf/CAVIARDATA2/TwoEnterShop3front/TwoEnterShop3front.mpg | 1075 | 00:00–00:43 (full clip) |

### Total footage

| Source | Clips | Duration |
|---|---|---|
| Pexels | 4 | ≈ 1 min |
| CAVIAR | 8 | ≈ 7.6 min |
| **Total** | **12** | **≈ 8.6 min** |

## Privacy

- No face recognition and no attempt to identify anyone. The system only detects and tracks anonymous person boxes.
- Faces are blurred in every published output frame, GIF or video.
