# GRC — Information Security Awareness video (v2)

A 7:24 Khmer training video narrated by **NTC**, the assistant of Ms. Sorn Leakena (GRC team), with English subtitles.
v2 (20 Nov 2026): the robot says the English words in its own voice (no second voice), and ISO is said "eye-so".

| File | What it is |
|---|---|
| `GRC_Security_Awareness_KH_v2.mp4` | Final video, 1920×1080, 25 fps, English subtitles drawn in |
| `GRC_Security_Awareness_KH_v2.srt` | The same English subtitles as a separate file (for YouTube / LMS) |
| `Security_Awareness_Training_Script_KM_EN.pdf` | Source script |
| `Security Awareness Training_V1.2.pptx` | The GRC slide deck (source of the newer video in `../SAT-Video`) |
| `video_v2/narration.json` | The 20 scenes: Khmer narration (`say`) and English subtitle (`sub`) |
| `video_v2/deck2.html`, `deck_base.css`, `icons.js` | Animated slides (each scene's animation lives in `window.FX`) |
| `video_v2/leakena_robot.svg` | The NTC robot |
| `video_v2/voice/` | Generated narration (Khmer female, natural style) and sentence timings |
| `video_v2/make_voice.py` | Regenerates `voice/` from `narration.json` (English words in the same voice) |
| `video_v2/make_grc_video.py` | Renders the video: `python make_grc_video.py render ../GRC_Security_Awareness_KH_v2.mp4` (or `preview 6,120,300` for still frames) |

The two scripts use the shared voice and render tool in `../video-tool`, which is kept locally and is not in this repository.
Only the latest version is kept here; version 1 is in the git history (commit 55532fc).
