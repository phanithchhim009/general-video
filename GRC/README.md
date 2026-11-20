# GRC — Information Security Awareness video

A 7:25 Khmer training video narrated by **NTC**, the assistant of Ms. Sorn Leakena (GRC team), with English subtitles.

| File | What it is |
|---|---|
| `GRC_Security_Awareness_KH.mp4` | Final video, 1920×1080, 25 fps, English subtitles drawn in |
| `GRC_Security_Awareness_KH.srt` | The same English subtitles as a separate file (for YouTube / LMS) |
| `Security_Awareness_Training_Script_KM_EN.pdf` | Source script |
| `video/narration.json` | The 20 scenes: Khmer narration (`say`) and English subtitle (`sub`) |
| `video/deck2.html`, `deck_base.css`, `icons.js` | Animated slides (each scene's animation lives in `window.FX`) |
| `video/leakena_robot.svg` | The NTC robot |
| `video/voice/` | Generated narration (Khmer female, natural style) and sentence timings |
| `video/make_voice.py` | Regenerates `voice/` from `narration.json` |
| `video/make_grc_video.py` | Renders the video: `python make_grc_video.py render ../GRC_Security_Awareness_KH.mp4` (or `preview 6,120,300` for still frames) |

The two scripts use the shared voice and render tool in `../video-tool`, which is kept locally and is not in this repository.
