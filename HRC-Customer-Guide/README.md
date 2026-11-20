# HRC — Customer App Guide video (Khmer, v2)

A Khmer how-to video for the Help Road Cambodia customer app, presented by **HRC**, the orange mechanic robot,
with English subtitles. It opens with a short cartoon story that also works as a stand-alone advert.

| File | What it is |
|---|---|
| `HRC_Customer_App_Guide_KH_v2.mp4` (+ `.srt`) | Full guide (7:04): story → HRC intro → 6-step process flow → every step on the phone → tips → recap → thanks |
| `HRC_Story_Ad_KH_v2.mp4` (+ `.srt`) | Only the cartoon story (flat tire → HRC app → mechanic → ride on), 38 s, for marketing |
| `video_v2/narration.json` | The 21 scenes: Khmer narration (`say`) and English subtitle (`sub`) |
| `video_v2/deck.html` | Everything that moves: the cartoon (SVG), the process-flow road, the phone engine (screens, finger taps, highlights, typing, radar, QR scan, SOS hold) and the step slides |
| `video_v2/hrc_robot.svg` | The HRC robot |
| `video_v2/screens/` | Real customer-app screens (mock build, 12 Nov 2026), "(demo)" buttons painted out, customer name ផានិត |
| `video_v2/make_voice.py` | Khmer voice (km-female, natural style; English words in the same voice) → `video_v2/voice/` |
| `video_v2/make_video.py` | Renders the video (`preview 5,40,90` for still frames; `sound check.wav story1,story2` for only the sound track) |

```
cd video_v2
..\..\video-tool\tools\tts-venv\Scripts\python.exe make_voice.py        # only after narration.json changes (delete the scene's wav first)
python make_video.py preview 5,40,90
python make_video.py render ..\HRC_Customer_App_Guide_KH_v2.mp4
python make_video.py render ..\HRC_Story_Ad_KH_v2.mp4 story1,story2
```

v2 (20 Nov 2026): motorbike engine sound in the cartoon (`engine_track()` in make_video.py); the customer is called
**ផានិត (Phanith)**; English words are spoken by the same robot voice (`voice.say(..., en='same')`); the payment scene says
"ABA or other banks". Phone actions live in `PH` in `deck.html`: coordinates are screenshot pixels (618 × 1350); times
are seconds, `cN` = when sentence N of the scene's voice starts (`c2+0.5`), or `fX` = fraction of the voice.

Only the latest version is kept here; version 1 is in the git history (commit 21bb5e4).
The scripts use the shared voice and render tool in `../video-tool`, which is kept locally and is not in this repository.
