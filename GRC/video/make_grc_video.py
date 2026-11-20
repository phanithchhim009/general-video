"""GRC Information Security Awareness video, presented by the robot Sorn Leakena.

  python make_grc_video.py preview 3,20,60      -> preview/t003.0.png ... (check the look at given seconds)
  python make_grc_video.py render ..\\GRC_Security_Awareness_KH.mp4   (+ .srt English subtitles)

Voice: voice/<id>.wav from make_voice.py (km-female, natural style, General Video/video-tool/voice.py).
Slides: deck2.html (animated per frame by seek(t), scene animations in its FX object); robot: leakena_robot.svg; script: narration.json.
Every frame is drawn by Edge (headless, DevTools protocol) at an exact time, so animations are smooth."""
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

lines = json.loads((HERE / 'narration.json').read_text(encoding='utf-8'))
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
    # split after . ! ? : but never after a title such as "Ms." ("Ms. Sorn Leakena" was cut in two)
    parts = [p.strip() for p in re.split(r'(?<=[.!?:])(?<!Ms\.)(?<!Mr\.)(?<!Dr\.)\s+(?=[A-Z0-9"\'])', text) if p.strip()]
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
    lead = LEAD + (0.8 if n['id'] == 'intro' else 0)
    dur = round(lead + voice + TAIL + (1.6 if n['id'] == 'outro' else 0), 2)
    scenes.append({'id': n['id'], 'start': round(t, 2), 'dur': dur, 'lead': lead, 'voice': round(voice, 2), 'env': env,
                   'robot': n.get('robot', 'corner'), 'subs': sentence_chunks(n['sub'], t + lead, voice, cues), 'cues': cues})
    t += dur - X
TOTAL = round(t + X, 2)

# ---------------------------------------------------------------- the animated page
src = (HERE / 'deck2.html').read_text(encoding='utf-8')
robot = (HERE / 'leakena_robot.svg').read_text(encoding='utf-8').split('\n', 1)[1].rsplit('</svg>', 1)[0]
timeline = {'scenes': scenes, 'X': X, 'fps': FPS, 'total': TOTAL}
video_css = '''<style>
#robot{position:absolute;left:0;top:0;width:300px;height:380px;transform-origin:0 0;z-index:30;pointer-events:none}
#robot svg{overflow:visible}
</style>'''
video_js = '''<script>
const T = __TIMELINE__;
const secs = [...document.querySelectorAll('#stage .slide')];
if (secs.length !== T.scenes.length) document.title = 'SCENE COUNT MISMATCH ' + secs.length + ' vs ' + T.scenes.length;
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const ease = p => { p = clamp(p); return 1 - Math.pow(1 - p, 3); };
const back = p => { p = clamp(p); const c = 1.6; return 1 + (c + 1) * Math.pow(p - 1, 3) + c * Math.pow(p - 1, 2); };
// ---- per-slide plan: what appears when (spread over the narration on list slides)
const plan = secs.map((sec, i) => {
  const s = T.scenes[i];
  const items = [...sec.querySelectorAll('.a, .pop, .tog')];
  // Timing: data-cue="k" = when sentence k of the voice starts (+ data-d seconds), data-at="f" = at fraction f of the
  // voice; the section chip and the title come in at once, anything else follows quickly in page order.
  const cueT = k => s.lead + (s.cues[k] !== undefined ? s.cues[k] : k * s.voice / Math.max(1, s.cues.length || 1));
  const head = items.filter(el => el.classList.contains('chip') || el.tagName === 'H1');
  const rest = items.filter(el => !head.includes(el) && el.dataset.cue === undefined && el.dataset.at === undefined);
  const delay = el => {
    if (el.dataset.cue !== undefined) return cueT(+el.dataset.cue) + (+el.dataset.d || 0);
    if (el.dataset.at !== undefined) return s.lead + (+el.dataset.at) * s.voice + (+el.dataset.d || 0);
    const h = head.indexOf(el);
    if (h >= 0) return 0.2 + h * 0.15;
    return 0.55 + rest.indexOf(el) * 0.14;
  };
  const anim = items.map(el => ({ el, d: delay(el), pop: el.classList.contains('pop'), tog: el.classList.contains('tog'),
                                  off: el.dataset.off === '1', base: el.style.transform || '' }));
  const dOf = el => { const a = anim.find(x => x.el === el || x.el.contains(el)); return a ? a.d : 0.3; };
  const counts = [...sec.querySelectorAll('[data-count]')].map(el => ({ el, v: +el.dataset.count, d: dOf(el) + 0.2 }));
  const bars = [...sec.querySelectorAll('.bar')].map(el => ({ el, w: +el.dataset.w, d: dOf(el) + 0.25 }));
  const ticks = anim.filter(a => a.el.dataset.tick !== undefined).map(a => ({ el: a.el, d: a.d + 0.8 }));
  return { anim, counts, bars, ticks, cueT };
});
// ---- background network (ISP theme): drifting nodes, links between near ones
const bg = document.getElementById('bg');
const NODES = Array.from({ length: 26 }, (_, k) => ({ x: (k * 397) % 1920, y: (k * 263 + 90) % 1080, p: k * 1.7, r: 2 + (k % 3) }));
function drawBg(t) {
  const pts = NODES.map(n => ({ x: n.x + Math.sin(t * 0.12 + n.p) * 40, y: n.y + Math.cos(t * 0.1 + n.p) * 30, r: n.r }));
  let h = '';
  for (let a = 0; a < pts.length; a++) for (let b = a + 1; b < pts.length; b++) {
    const d = Math.hypot(pts[a].x - pts[b].x, pts[a].y - pts[b].y);
    if (d < 330) h += `<line x1="${pts[a].x.toFixed(1)}" y1="${pts[a].y.toFixed(1)}" x2="${pts[b].x.toFixed(1)}" y2="${pts[b].y.toFixed(1)}" stroke="#7FA6CF" stroke-opacity="${(0.14 * (1 - d / 330)).toFixed(3)}" stroke-width="1"/>`;
  }
  pts.forEach((p, k) => { const pulse = 0.25 + 0.15 * Math.sin(t * 0.8 + k); h += `<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="${p.r * 0.8}" fill="#9CC3E6" fill-opacity="${pulse.toFixed(2)}"/>`; });
  bg.innerHTML = h;
}
const robot = document.getElementById('robot');
const R = id => document.getElementById(id);
const subs = document.getElementById('subs');
const POS = { hero: [250, 200, 1.72], corner: [1748, 858, 0.5], outro: [1330, 250, 1.45] };
function seek(t) {
  let cur = 0;
  drawBg(t);
  document.getElementById('progress').style.width = (100 * clamp(t / T.total)) + '%';
  T.scenes.forEach((s, i) => {
    const sec = secs[i], lt = t - s.start;
    let op = Math.min(i === 0 ? 1 : clamp(lt / T.X), i === T.scenes.length - 1 ? 1 : clamp((s.start + s.dur - t) / T.X));
    if (lt < 0 || lt > s.dur) op = 0;
    sec.style.opacity = op; sec.style.visibility = op > 0 ? 'visible' : 'hidden';
    sec.style.transform = `scale(${1 + 0.025 * (1 - ease(lt / 1.2))})`;
    if (op > 0 && lt >= 0) cur = i;
    if (op <= 0) return;
    const p = plan[i];
    p.anim.forEach(a => {
      if (a.tog) {
        const on = (lt >= a.d) !== a.off;
        a.el.style.background = on ? '#10B981' : '#334155';
        const k = a.el.firstElementChild; if (k) k.style.transform = `translateX(${on ? 28 : 0}px)`;
        return;
      }
      if (a.pop) { const e = back((lt - a.d) / 0.55); a.el.style.opacity = clamp((lt - a.d) / 0.3); a.el.style.transform = `${a.base} scale(${0.6 + 0.4 * e})`; return; }
      const e = ease((lt - a.d) / 0.7);
      a.el.style.opacity = e; a.el.style.transform = `${a.base} translateY(${(1 - e) * 40}px)`;
    });
    p.counts.forEach(c => { const e = ease((lt - c.d) / 1.2); c.el.textContent = Math.round(c.v * e); });
    p.bars.forEach(b => { const e = ease((lt - b.d) / 1.4); b.el.style.width = (b.w * e) + '%'; });
    p.ticks.forEach(k => k.el.classList.toggle('on', lt >= k.d));
    const fx = window.FX && window.FX[s.id];
    if (fx) fx({ lt, s, sec, cue: p.cueT, at: f => s.lead + f * s.voice, p: (t0, d) => ease((lt - t0) / d) });
  });
  // subtitles (English)
  const s = T.scenes[cur];
  const chunk = s.subs.find(c => t >= c.t0 && t < c.t1 + 0.25);
  if (chunk) { if (subs.textContent !== chunk.text) subs.textContent = chunk.text; subs.style.opacity = clamp(Math.min((t - chunk.t0) / 0.2, (chunk.t1 + 0.25 - t) / 0.2)); }
  else subs.style.opacity = 0;
  // robot: moves between hero / corner / outro, floats, blinks, talks, waves; Wi-Fi waves pulse while talking
  const prev = T.scenes[Math.max(0, cur - 1)];
  const k = ease((t - s.start) / 1.2);
  const [x0, y0, z0] = POS[prev.robot], [x1, y1, z1] = POS[s.robot];
  const [x, y, z] = cur === 0 ? [x1, y1, z1] : [x0 + (x1 - x0) * k, y0 + (y1 - y0) * k, z0 + (z1 - z0) * k];
  const enter = ease(t / 1.3);
  robot.style.transform = `translate(${x - (1 - enter) * 600}px, ${y + Math.sin(t * 2.1) * 8 * z}px) scale(${z}) rotate(${Math.sin(t * 1.3) * 1.5}deg)`;
  robot.style.opacity = enter;
  const blink = (t % 3.9) < 0.14 || ((t + 1.7) % 8.3) < 0.12;
  R('r-eyes').setAttribute('transform', blink ? 'translate(0 113) scale(1 0.1) translate(0 -113)' : '');
  const vt = t - s.start - s.lead, f = Math.floor(vt * T.fps);
  const open = vt >= 0 && f < s.env.length ? s.env[f] : 0;
  const mh = 5 + 15 * open, mw = 26 + 8 * open;   // a rounded mouth, a little wider and taller with the voice
  const m = R('r-mouth'); m.setAttribute('height', mh); m.setAttribute('y', 150 - mh / 2); m.setAttribute('width', mw); m.setAttribute('x', 150 - mw / 2);
  m.setAttribute('rx', Math.min(mw, mh) / 2); m.setAttribute('ry', mh / 2);
  R('r-antenna-light').setAttribute('fill', open > 0.15 ? '#CFFAFE' : '#22D3EE');
  R('r-antenna-glow').setAttribute('opacity', 0.4 + 0.6 * Math.abs(Math.sin(t * 3)));
  R('r-wifi').setAttribute('opacity', (0.35 + 0.65 * Math.max(open, 0.5 + 0.5 * Math.sin(t * 4))).toFixed(2));
  const waving = s.robot === 'hero' ? clamp(Math.min(t / 0.5, (s.lead + 3.2 - (t - s.start)) / 0.5))
               : s.robot === 'outro' ? clamp((t - s.start - s.lead - s.voice + 3.5) / 0.5) : 0;
  R('r-arm-r').setAttribute('transform', `rotate(${waving * (-150 + 22 * Math.sin(t * 9))} 239 222)`);
  return cur;
}
window.seek = seek;
seek(0);
</script>'''.replace('__TIMELINE__', json.dumps(timeline))
src = src.replace('</head>', video_css + '\n</head>', 1)
src = src.replace('<div id="stage">', f'<div id="stage">\n<div id="robot"><svg viewBox="0 0 300 380" width="300" height="380">{robot}</svg></div>', 1)
src = src.replace('</body>', video_js + '\n</body>', 1)
PAGE = HERE / '_video.html'
PAGE.write_text(src, encoding='utf-8')


# ---------------------------------------------------------------- Edge via the DevTools protocol
class Edge:
    def __init__(self):
        import websocket
        prof = HERE / '_edge_profile'
        self.proc = subprocess.Popen([EDGE, '--headless=new', '--remote-debugging-port=9342', '--remote-allow-origins=*', '--no-first-run',
                                      '--hide-scrollbars', '--force-device-scale-factor=1', '--window-size=1920,1080',
                                      f'--user-data-dir={prof}', 'about:blank'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        pages = []
        for _ in range(100):
            try:
                pages = [p for p in json.load(opener.open('http://127.0.0.1:9342/json/list')) if p['type'] == 'page']
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

    def shot(self, t, path, fmt='jpeg'):
        self.js(f'seek({t:.3f})')
        data = self.call('Page.captureScreenshot', format=fmt, quality=92, fromSurface=True)['data']
        Path(path).write_bytes(base64.b64decode(data))

    def close(self):
        self.ws.close()
        self.proc.kill()


def ts(x):
    ms = int(round(x * 1000))
    return f'{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}'


mode = sys.argv[1]
print('scenes:', [(s['id'], s['start'], round(s['dur'], 1)) for s in scenes])
print(f'total {TOTAL:.0f}s ({int(TOTAL // 60)}:{int(TOTAL % 60):02d})')
edge = Edge()
edge.open('file:///' + str(PAGE).replace('\\', '/'))
if mode == 'preview':
    out = HERE / 'preview'
    out.mkdir(exist_ok=True)
    for x in sys.argv[2].split(','):
        edge.shot(float(x), out / f't{float(x):05.1f}.png', 'png')
    edge.close()
    sys.exit(0)

target = Path(sys.argv[2]).resolve()
frames = HERE / '_frames'
shutil.rmtree(frames, ignore_errors=True)
frames.mkdir()
count = int(TOTAL * FPS)
t0 = time.time()
for i in range(count):
    edge.shot(i / FPS, frames / f'{i:05d}.jpg')
    if i % 500 == 0:
        print(f'frame {i}/{count}  {time.time() - t0:.0f}s', flush=True)
edge.close()

args = [str(FF / 'ffmpeg.exe'), '-y', '-hide_banner', '-loglevel', 'error', '-framerate', str(FPS), '-i', str(frames / '%05d.jpg')]
for s in scenes:
    args += ['-i', str(vdir / f"{s['id']}.wav")]
fx = [f'[0:v]fade=t=in:st=0:d=0.6,fade=t=out:st={TOTAL - 1.0:.2f}:d=1.0,format=yuv420p[v]']
for i, s in enumerate(scenes):
    fx.append(f'[{i + 1}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int((s["start"] + s["lead"]) * 1000)}:all=1[a{i}]')
fx.append(''.join(f'[a{i}]' for i in range(len(scenes))) + f'amix=inputs={len(scenes)}:normalize=0,apad,atrim=0:{TOTAL:.2f}[a]')
args += ['-filter_complex', ';'.join(fx), '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-preset', 'slow', '-crf', '18',
         '-r', str(FPS), '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', str(target)]
subprocess.run(args, check=True)

subs = [c for s in scenes for c in s['subs']]
target.with_suffix('.srt').write_text('\n'.join(f"{i + 1}\n{ts(c['t0'])} --> {ts(c['t1'])}\n{c['text']}\n" for i, c in enumerate(subs)), encoding='utf-8')
shutil.rmtree(frames, ignore_errors=True)
PAGE.unlink(missing_ok=True)
print(f'{target}  {TOTAL:.0f}s, {count} frames, {time.time() - t0:.0f}s')
