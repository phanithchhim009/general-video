# HRC — Customer App Guide video (Khmer)

A Khmer how-to video for the Help Road Cambodia customer app, presented by **HRC**, the orange mechanic robot,
with English subtitles. It opens with a short cartoon story that also works as a stand-alone advert.

| File | What it is |
|---|---|
| `HRC_Customer_App_Guide_KH.mp4` (+ `.srt`) | Full guide: story → HRC intro → 6-step process flow → every step on the phone → tips → recap → thanks |
| `HRC_Story_Ad_KH.mp4` (+ `.srt`) | Only the cartoon story (flat tire → HRC app → mechanic → ride on), for marketing |
| `video/narration.json` | The 21 scenes: Khmer narration (`say`) and English subtitle (`sub`) |
| `video/deck.html` | Everything that moves: the cartoon (SVG), the process-flow road, the phone engine (screens, finger taps, highlights, typing, radar, QR scan, SOS hold) and the step slides |
| `video/hrc_robot.svg` | The HRC robot |
| `video/screens/` | Real customer-app screens (mock build, 12 Nov 2026), "(demo)" buttons painted out — made by `prep_screens.py` |
| `video/make_voice.py` | Khmer voice (km-female, natural style) → `video/voice/` |
| `video/make_video.py` | Renders the video (`preview 5,40,90` for still frames) |

```
cd video
..\..\video-tool\tools\tts-venv\Scripts\python.exe make_voice.py        # only after narration.json changes (delete the scene's wav first)
python make_video.py preview 5,40,90
python make_video.py render ..\HRC_Customer_App_Guide_KH.mp4
python make_video.py render ..\HRC_Story_Ad_KH.mp4 story1,story2
```

## Version 2 (`video_v2/`, 20 Nov 2026)

`HRC_Customer_App_Guide_KH_v2.mp4` and `HRC_Story_Ad_KH_v2.mp4` (+ `.srt`). Version 1 stays as it is in `video/`.

- Motorbike engine sound in the cartoon (made in `make_video.py` → `engine_track()`): riding, sputtering out after the
  tire bursts, the HRC mechanic arriving and stopping, riding off. `python make_video.py sound check.wav story1,story2`
  writes only the sound track.
- The customer is called **ផានិត (Phanith)** instead of សុខា: narration, subtitles, the typed name on the profile screen and
  the greeting on the home screen (a `label` action in `PH`).
- English words are spoken by the **same robot voice** with English pronunciation (`voice.say(..., en='same')`;
  abbreviations as English letter names, e.g. HRC → "aitch ar see"), not by a second English voice.

Phone actions live in `PH` in `deck.html`: coordinates are screenshot pixels (618 × 1350); times are seconds,
`cN` = when sentence N of the scene's voice starts (`c2+0.5`), or `fX` = fraction of the voice.
This project is separate from `GRC/` and is not part of the public general-video repository (`.gitignore`).
