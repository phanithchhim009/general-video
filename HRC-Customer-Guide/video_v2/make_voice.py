"""Khmer voice clips for the HRC customer-app guide: voice/<id>.wav (km-female, natural style; English words in the same voice, en='same') + durations.json."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent.parent / 'video-tool'))
import voice  # noqa: E402

lines = json.loads((HERE / 'narration.json').read_text(encoding='utf-8'))
out = HERE / 'voice'
out.mkdir(exist_ok=True)
durations = {}
for n in lines:
    wav = out / f"{n['id']}.wav"
    if not wav.exists():
        voice.say('km-female', n['say'], wav, 'natural', en='same')   # v2: English words in the same voice
    import soundfile as sf
    info = sf.info(wav)
    durations[n['id']] = round(info.frames / info.samplerate, 2)
    print(f"{n['id']:10} {durations[n['id']]:6.1f}s", flush=True)
(out / 'durations.json').write_text(json.dumps(durations, indent=2))
print(f"voice total {sum(durations.values()):.0f}s")
