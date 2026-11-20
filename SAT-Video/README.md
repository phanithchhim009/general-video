# Security Awareness Training v1.2 — Khmer video

Made only from `Security Awareness Training_V1.2.pptx` (GRC team, 23 slides), with new animated UI.
Khmer voice (one voice; English words said the English way, ISO = "eye-so"), English subtitles,
presented by the GRC robot (no name — it says "ខ្ញុំជា Robot").

| File | What it is |
|---|---|
| `SAT_v1.2_KH.mp4` (+ `.srt`) | The video, 1920×1080, about 8:52 |
| `video/narration.json` | 23 scenes, one per slide: Khmer narration (`say`) + English subtitle (`sub`) |
| `video/deck.html` | All visuals: password-strength simulator, crack-time gauges, HTTP vs HTTPS browser, desk (Win+L lock), BYOD, classification chevrons, phishing SMS on an iPhone, the deck's phishing email with animated red flags, file-type wall, and the four Telegram steps on an iPhone (iOS screens in `SCR`, step-by-step taps in `FLOWS`) |
| `video/robot.svg` | GRC robot (badge "GRC") |
| `video/img/` | Pictures taken from the .pptx (phishing email, quiz QR) |

```
cd video
..\..\video-tool\tools\tts-venv\Scripts\python.exe make_voice.py     # voice (delete a scene's wav to redo it)
python make_video.py preview 20,120,300                               # still frames
python make_video.py render ..\SAT_v1.2_KH.mp4
```

## PowerPoint v2.0 in the video's look

`Security Awareness Training_V2.0.pptx` — 23 slides, same order as v1.2. Titles, bullets, cards, numbers and the
classification chevrons are editable PowerPoint shapes (Khmer: Khmer OS Siemreap / Battambang, Latin: Segoe UI);
phones, simulators and icons are the video's visuals. Fade transitions (push on the Telegram steps), items appear one
after another automatically, and each slide's speaker notes hold the video's Khmer narration + English text.

```
cd pptx_v2
python capture.py        # visuals from ../video/_cap.html (copy of the page make_video.py builds) -> cap/
python build_pptx.py     # -> ../Security Awareness Training_V2.0.pptx
```

Not part of the public general-video repository (only `GRC/` is published).
