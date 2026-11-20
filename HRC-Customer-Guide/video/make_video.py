"""HRC customer-app guide video (Khmer voice, English subtitles), presented by the robot HRC.

  python make_video.py preview 3,20,60                          -> preview/t003.0.png ... (check the look at given seconds)
  python make_video.py render ..\\HRC_Customer_App_Guide_KH.mp4  (+ .srt English subtitles)
  python make_video.py render ..\\HRC_Story_Ad_KH.mp4 story1,story2   (only these scenes: the short cartoon advert)

Voice: voice/<id>.wav from make_voice.py (km-female, natural style, General Video/video-tool/voice.py).
Slides: deck.html (cartoon story, process-flow road, phone screens with taps; scene animations in its FX object);
robot: hrc_robot.svg; script: narration.json; app screens: screens/ (prep_screens.py).
Every frame is drawn by Edge (headless, DevTools protocol) at an exact time, so animations are smooth.
Based on GRC/video/make_grc_video.py (same renderer, own copy so the GRC project stays unchanged)."""
import base64
import json
import math
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
FF = HERE.parent.parent / 'video-tool' / 'tools' / 'ffmpeg'
EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
FPS, X = 25, 0.7                 # frame rate, cross-fade between slides (s)
LEAD, TAIL = 0.9, 1.1            # silence before / after each line (s)
EXTRA_LEAD = {'story1': 1.8, 'intro': 0.8}
EXTRA_TAIL = {'story2': 1.6, 'outro': 1.6}

mode = sys.argv[1]
lines = json.loads((HERE / 'narration.json').read_text(encoding='utf-8'))
ONLY = sys.argv[3].split(',') if mode == 'render' and len(sys.argv) > 3 else None
vdir = HERE / 'voice'


def envelope(wav):
    """Mouth openness 0..1 per video frame, from the voice loudness."""
    pcm = subprocess.run([str(FF / 'ffmpeg.exe'), '-v', 'error', '-i', str(wav), '-ac', '1', '-ar', '8000', '-f', 's16le', '-'],
                         capture_output=True, check=True).stdout
    samples = memoryview(pcm).cast('h')
    win = 8000 // FPS
    rms = [math.sqrt(sum(s * s for s in samples[i:i + win]) / max(1, len(samples[i:i + win]))) for i in range(0, len(samples), win)]
    peak = sorted(rms)[int(len(rms) * 0.98)] or 1
    return [round(min(1.0, (r / peak) ** 0.8 * 1.15), 2) for r in rms]


def sentence_chunks(text, start, length, cues=()):
    """English subtitle chunks: on the Khmer sentence starts when the counts match, else in proportion to their length."""
    parts = [p.strip() for p in re.split(r'(?<=[.!?])\s+(?=[A-Z0-9"\'])', text) if p.strip()]
    merged = []
    for p in parts:   # very short pieces join the next one
        if merged and len(merged[-1]) < 38:
            merged[-1] += ' ' + p
        else:
            merged.append(p)
    if cues and len(cues) == len(merged):
        ends = list(cues[1:]) + [length]
        return [{'t0': round(start + a, 2), 't1': round(start + b, 2), 'text': p} for p, a, b in zip(merged, cues, ends)]
    total = sum(len(p) for p in merged) or 1
    out, t = [], start
    for p in merged:
        d = length * len(p) / total
        out.append({'t0': round(t, 2), 't1': round(t + d, 2), 'text': p})
        t += d
    return out


scenes, t = [], 0.0
for n in lines:
    wav = vdir / f"{n['id']}.wav"
    cue_file = vdir / f"{n['id']}.cues.json"
    cues = json.loads(cue_file.read_text()) if cue_file.exists() else []
    env = envelope(wav)
    voice = len(env) / FPS
    lead = LEAD + EXTRA_LEAD.get(n['id'], 0)
    dur = round(lead + voice + TAIL + EXTRA_TAIL.get(n['id'], 0), 2)
    scenes.append({'id': n['id'], 'start': round(t, 2), 'dur': dur, 'lead': lead, 'voice': round(voice, 2), 'env': env,
                   'robot': n.get('robot', 'corner'), 'subs': sentence_chunks(n['sub'], t + lead, voice, cues), 'cues': cues,
                   'show': not ONLY or n['id'] in ONLY})
    t += dur - X
TOTAL_ALL = round(t + X, 2)

# Only some scenes (e.g. the cartoon advert): the page keeps every slide, the render takes just their time span.
shown = [s for s in scenes if s['show']]
T0 = shown[0]['start']
TOTAL = round(shown[-1]['start'] + shown[-1]['dur'] - T0, 2)
s1 = scenes[0]
BANG = s1['start'] + s1['lead'] + (s1['cues'][2] if len(s1['cues']) > 2 else 6) - 0.6   # = deck.html storyTimes() TB

# ---------------------------------------------------------------- the animated page
src = (HERE / 'deck.html').read_text(encoding='utf-8')
robot = (HERE / 'hrc_robot.svg').read_text(encoding='utf-8').split('\n', 1)[1].rsplit('</svg>', 1)[0]
timeline = {'scenes': scenes, 'X': X, 'fps': FPS, 'total': TOTAL_ALL}
video_css = '''<style>
#robot{position:absolute;left:0;top:0;width:300px;height:380px;transform-origin:0 0;z-index:30;pointer-events:none}
#robot svg{overflow:visible}
</style>'''
video_js = '''<script>
const T = __TIMELINE__;
const secs = [...document.querySelectorAll('#stage .slide')];
if (secs.length !== T.scenes.length) document.title = 'SCENE COUNT MISMATCH ' + secs.length + ' vs ' + T.scenes.length;
secs.forEach((s, i) => { if (T.scenes[i] && s.dataset.id !== T.scenes[i].id) document.title = 'SCENE ORDER MISMATCH ' + s.dataset.id + ' vs ' + T.scenes[i].id; });
// ---- per-slide plan: what appears when (data-cue="k" = when sentence k of the voice starts, + data-d seconds)
const plan = secs.map((sec, i) => {
  const s = T.scenes[i];
  const items = [...sec.querySelectorAll('.a, .pop')];
  const cueT = k => s.lead + (s.cues[k] !== undefined ? s.cues[k] : k * s.voice / Math.max(1, s.cues.length || 1));
  const head = items.filter(el => el.classList.contains('chip') || el.tagName === 'H1');
  const rest = items.filter(el => !head.includes(el) && el.dataset.cue === undefined);
  const delay = el => {
    if (el.dataset.cue !== undefined) return cueT(+el.dataset.cue) + (+el.dataset.d || 0);
    const h = head.indexOf(el);
    if (h >= 0) return 0.2 + h * 0.15;
    return 0.55 + rest.indexOf(el) * 0.14;
  };
  const anim = items.map(el => ({ el, d: delay(el), pop: el.classList.contains('pop'), base: el.style.transform || '' }));
  return { anim, cueT };
});
const robot = document.getElementById('robot');
const R = id => document.getElementById(id);
const subs = document.getElementById('subs');
const brand = document.getElementById('brand'), flowbar = document.getElementById('flowbar');
const POS = { hero: [250, 210, 1.72], corner: [1748, 858, 0.5], outro: [1330, 250, 1.45], off: [2300, 858, 0.5] };
function seek(t) {
  let cur = 0;
  drawBg(t);
  document.getElementById('progress').style.width = (100 * clamp(t / T.total)) + '%';
  let storyOp = 0, phaseOp = 0;
  T.scenes.forEach((s, i) => {
    const sec = secs[i], lt = t - s.start;
    let op = Math.min(i === 0 ? 1 : clamp(lt / T.X), i === T.scenes.length - 1 ? 1 : clamp((s.start + s.dur - t) / T.X));
    if (lt < 0 || lt > s.dur) op = 0;
    sec.style.opacity = op; sec.style.visibility = op > 0 ? 'visible' : 'hidden';
    if (!sec.classList.contains('story')) sec.style.transform = `scale(${1 + 0.02 * (1 - ease(lt / 1.2))})`;
    if (op > 0 && lt >= 0) cur = i;
    if (sec.classList.contains('story')) storyOp = Math.max(storyOp, op);
    if (op <= 0) return;
    if (sec.dataset.phase) { phaseOp = Math.max(phaseOp, op); if (op >= 0.5) setPhase(+sec.dataset.phase); }
    const p = plan[i];
    p.anim.forEach(a => {
      if (a.pop) { const e = back((lt - a.d) / 0.55); a.el.style.opacity = clamp((lt - a.d) / 0.3); a.el.style.transform = `${a.base} scale(${0.6 + 0.4 * e})`; return; }
      const e = ease((lt - a.d) / 0.7);
      a.el.style.opacity = e; a.el.style.transform = `${a.base} translateY(${(1 - e) * 40}px)`;
    });
    const fx = window.FX && window.FX[s.id];
    if (fx) fx({ lt, s, sec, cue: p.cueT, at: f => s.lead + f * s.voice });
  });
  brand.style.opacity = 1 - storyOp;
  flowbar.style.opacity = phaseOp;
  // subtitles (English): left column on the phone slides, centred elsewhere
  const s = T.scenes[cur];
  subs.className = secs[cur].querySelector('.phone:not(.sphone)') ? 'left' : 'center';
  const chunk = s.subs.find(c => t >= c.t0 && t < c.t1 + 0.25);
  if (chunk) { if (subs.textContent !== chunk.text) subs.textContent = chunk.text; subs.style.opacity = clamp(Math.min((t - chunk.t0) / 0.2, (chunk.t1 + 0.25 - t) / 0.2)); }
  else subs.style.opacity = 0;
  // robot: hidden in the cartoon, flies in for the intro, then hero / corner / outro; floats, blinks, talks, waves
  if (s.robot === 'off') { robot.style.opacity = 0; return cur; }
  const prev = T.scenes[Math.max(0, cur - 1)];
  const k = ease((t - s.start) / 1.2);
  const [x1, y1, z1] = POS[s.robot];
  const [x0, y0, z0] = prev.robot === 'off' ? [x1 - 700, y1 + 120, z1] : POS[prev.robot];
  const [x, y, z] = cur === 0 ? [x1, y1, z1] : [x0 + (x1 - x0) * k, y0 + (y1 - y0) * k, z0 + (z1 - z0) * k];
  robot.style.transform = `translate(${x}px, ${y + Math.sin(t * 2.1) * 8 * z}px) scale(${z}) rotate(${Math.sin(t * 1.3) * 1.5}deg)`;
  robot.style.opacity = prev.robot === 'off' && cur > 0 ? ease((t - s.start) / 0.9) : 1;
  const blink = (t % 3.9) < 0.14 || ((t + 1.7) % 8.3) < 0.12;
  R('r-eyes').setAttribute('transform', blink ? 'translate(0 128) scale(1 0.1) translate(0 -128)' : '');
  const vt = t - s.start - s.lead, f = Math.floor(vt * T.fps);
  const open = vt >= 0 && f < s.env.length ? s.env[f] : 0;
  const mh = 5 + 15 * open, mw = 26 + 8 * open;
  const m = R('r-mouth'); m.setAttribute('height', mh); m.setAttribute('y', 160 - mh / 2); m.setAttribute('width', mw); m.setAttribute('x', 150 - mw / 2);
  m.setAttribute('rx', Math.min(mw, mh) / 2); m.setAttribute('ry', mh / 2);
  R('r-antenna-light').setAttribute('fill', open > 0.15 ? '#FFEDD5' : '#FB923C');
  R('r-antenna-glow').setAttribute('opacity', 0.4 + 0.6 * Math.abs(Math.sin(t * 3)));
  R('r-wifi').setAttribute('opacity', (0.35 + 0.65 * Math.max(open, 0.5 + 0.5 * Math.sin(t * 4))).toFixed(2));
  const waving = s.robot === 'hero' ? clamp(Math.min((t - s.start - 0.4) / 0.5, (s.lead + 3.2 - (t - s.start)) / 0.5))
               : s.robot === 'outro' ? clamp((t - s.start - s.lead - s.voice + 3.5) / 0.5) : 0;
  R('r-arm-r').setAttribute('transform', `rotate(${waving * (-150 + 22 * Math.sin(t * 9))} 239 222)`);
  return cur;
}
window.seek = seek;
seek(0);
</script>'''.replace('__TIMELINE__', json.dumps(timeline))
src = src.replace('</head>', video_css + '\n</head>', 1)
src = src.replace('<div id="subs"', f'<div id="robot"><svg viewBox="0 0 300 380" width="300" height="380">{robot}</svg></div>\n<div id="subs"', 1)
src = src.replace('</body>', video_js + '\n</body>', 1)
PAGE = HERE / '_video.html'
PAGE.write_text(src, encoding='utf-8')


# ---------------------------------------------------------------- Edge via the DevTools protocol
class Edge:
    def __init__(self):
        import websocket
        prof = HERE / '_edge_profile'
        self.proc = subprocess.Popen([EDGE, '--headless=new', '--remote-debugging-port=9343', '--remote-allow-origins=*', '--no-first-run',
                                      '--hide-scrollbars', '--force-device-scale-factor=1', '--window-size=1920,1080',
                                      '--allow-file-access-from-files', f'--user-data-dir={prof}', 'about:blank'],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        pages = []
        for _ in range(100):
            try:
                pages = [p for p in json.load(opener.open('http://127.0.0.1:9343/json/list')) if p['type'] == 'page']
                if pages:
                    break
            except OSError:
                pass
            time.sleep(0.2)
        self.ws = websocket.create_connection(pages[0]['webSocketDebuggerUrl'], suppress_origin=True, max_size=None)
        self.n = 0
        self.call('Emulation.setDeviceMetricsOverride', width=1920, height=1080, deviceScaleFactor=1, mobile=False)

    def call(self, method, **params):
        self.n += 1
        self.ws.send(json.dumps({'id': self.n, 'method': method, 'params': params}))
        while True:
            m = json.loads(self.ws.recv())
            if m.get('id') == self.n:
                if 'error' in m:
                    raise RuntimeError(m['error'])
                return m.get('result', {})

    def js(self, expr):
        return self.call('Runtime.evaluate', expression=expr, returnByValue=True).get('result', {}).get('value')

    def open(self, url):
        self.call('Page.navigate', url=url)
        for _ in range(150):
            if self.js("document.readyState==='complete' && document.fonts.status==='loaded' && typeof seek==='function'"):
                break
            time.sleep(0.2)
        time.sleep(1.5)                          # images and web fonts settle
        title = self.js('document.title')
        if 'MISMATCH' in (title or ''):
            raise SystemExit(title)

    def errors(self):
        return self.js('JSON.stringify(window.__errs||[])')

    def shot(self, t, path, fmt='jpeg'):
        r = self.call('Runtime.evaluate', expression=f'seek({t:.3f})', returnByValue=True)
        if 'exceptionDetails' in r:
            raise RuntimeError(f"seek({t}) failed: {r['exceptionDetails'].get('exception', {}).get('description', r['exceptionDetails'])}")
        data = self.call('Page.captureScreenshot', format=fmt, quality=92, fromSurface=True)['data']
        Path(path).write_bytes(base64.b64decode(data))

    def close(self):
        self.ws.close()
        self.proc.kill()


def ts(x):
    ms = int(round(x * 1000))
    return f'{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}'


print('scenes:', [(s['id'], s['start'], round(s['dur'], 1)) for s in scenes])
print(f'total {TOTAL:.0f}s ({int(TOTAL // 60)}:{int(TOTAL % 60):02d})')
edge = Edge()
edge.open('file:///' + str(PAGE).replace('\\', '/'))
print('page errors:', edge.errors())
if mode == 'preview':
    out = HERE / 'preview'
    out.mkdir(exist_ok=True)
    for x in sys.argv[2].split(','):
        edge.shot(float(x), out / f't{float(x):05.1f}.png', 'png')
    print('page errors:', edge.errors())
    edge.close()
    sys.exit(0)

target = Path(sys.argv[2]).resolve()
frames = HERE / '_frames'
shutil.rmtree(frames, ignore_errors=True)
frames.mkdir()
count = int(TOTAL * FPS)
t0 = time.time()
for i in range(count):
    edge.shot(T0 + i / FPS, frames / f'{i:05d}.jpg')
    if i % 500 == 0:
        print(f'frame {i}/{count}  {time.time() - t0:.0f}s', flush=True)
print('page errors:', edge.errors())
edge.close()

# the tire "bang": a short low thump with a noise burst (made here, no sound files needed)
bang = HERE / '_bang.wav'
subprocess.run([str(FF / 'ffmpeg.exe'), '-y', '-v', 'error', '-f', 'lavfi', '-i', 'anoisesrc=d=0.7:c=pink:a=0.9:r=48000',
                '-f', 'lavfi', '-i', 'sine=f=55:d=0.5:sample_rate=48000', '-filter_complex',
                '[0]afade=t=out:st=0.02:d=0.6,lowpass=f=2400[n];[1]volume=2.2,afade=t=out:st=0:d=0.45[s];'
                '[n][s]amix=inputs=2:normalize=0,volume=0.8,aformat=channel_layouts=stereo', str(bang)], check=True)

args = [str(FF / 'ffmpeg.exe'), '-y', '-hide_banner', '-loglevel', 'error', '-framerate', str(FPS), '-i', str(frames / '%05d.jpg')]
for s in shown:
    args += ['-i', str(vdir / f"{s['id']}.wav")]
fx = [f'[0:v]fade=t=in:st=0:d=0.6,fade=t=out:st={TOTAL - 1.0:.2f}:d=1.0,format=yuv420p[v]']
for i, s in enumerate(shown):
    fx.append(f'[{i + 1}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int((s["start"] - T0 + s["lead"]) * 1000)}:all=1[a{i}]')
mix, n_in = ''.join(f'[a{i}]' for i in range(len(shown))), len(shown)
if scenes[0]['show']:
    args += ['-i', str(bang)]
    fx.append(f'[{n_in + 1}:a]adelay={int((BANG - T0) * 1000)}:all=1[bang]')
    mix += '[bang]'
    n_in += 1
fx.append(mix + f'amix=inputs={n_in}:normalize=0,apad,atrim=0:{TOTAL:.2f}[a]')
args += ['-filter_complex', ';'.join(fx), '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-preset', 'slow', '-crf', '18',
         '-r', str(FPS), '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', str(target)]
subprocess.run(args, check=True)

subs = [c for s in shown for c in s['subs']]
target.with_suffix('.srt').write_text('\n'.join(f"{i + 1}\n{ts(c['t0'] - T0)} --> {ts(c['t1'] - T0)}\n{c['text']}\n" for i, c in enumerate(subs)), encoding='utf-8')
shutil.rmtree(frames, ignore_errors=True)
PAGE.unlink(missing_ok=True)
bang.unlink(missing_ok=True)
print(f'{target}  {TOTAL:.0f}s, {count} frames, {time.time() - t0:.0f}s')
