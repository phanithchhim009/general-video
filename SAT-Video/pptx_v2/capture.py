"""Takes the visuals of the SAT video (phones, simulators, icons, robot) as transparent PNGs for the PowerPoint version.

  python capture.py        -> cap/<name>.png

Uses ../video/_cap.html (a copy of the page the renderer builds) in its own headless Edge (port 9350), so it can run
while a video render is going. Each shot = (name, scene id, time, CSS selector inside that scene's slide).
Time: 'end' (just before the scene fades out) or 'cK+d' (sentence K of the scene's voice + d seconds)."""
import base64
import json
import subprocess
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
PAGE = HERE.parent / 'video' / '_cap.html'
OUT = HERE / 'cap'
EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
PORT = 9350

SHOTS = [
    ('robot', 'intro', 'end', '#robot svg'),
    ('intro_shield', 'intro', 'end', '#intro-shield'),
    ('what_radar', 'what', 'end', '#radar'), ('what_data', 'what', 'end', '#datash'), ('what_habit', 'what', 'end', '#habit'),
    *[(f'best_{i}', 'best', 'end', f'.card:nth-child({i}) > svg') for i in range(1, 5)],
    ('pw_window', 'password', 'end', '.vis .win'),
    *[(f'gauge_{i}', 'crack', 'end', f'#gauges > .card:nth-child({i}) svg.g') for i in range(1, 4)],
    ('net', 'internet', 'end', '#net'),
    ('desk', 'desk', 'end', '#deskv svg'),
    ('byod', 'byod', 'end', '#byodv svg'),
    ('phish_phone', 'phishing', 'end', '.iphone'),
    ('phish_email', 'checks', 'end', '.win'),
    *[(f'act_{i}', 'email', 'end', f'#acts > .card:nth-child({i}) svg') for i in range(1, 5)],
    ('bad_files', 'files', 'end', '#bad-files'), ('ok_files', 'files', 'end', '#ok-files'),
    ('tg_overview', 'telegram', 'c1+1.0', '.iphone'),
    ('tg2fa_1', 'tg2fa', 'c1+1.3', '.iphone'), ('tg2fa_2', 'tg2fa', 'c2+1.9', '.iphone'), ('tg2fa_3', 'tg2fa', 'c4-0.7', '.iphone'),
    ('tg2fa_4', 'tg2fa', 'c5-1.1', '.iphone'), ('tg2fa_5', 'tg2fa', 'end', '.iphone'),
    ('tgs_1', 'tgsessions', 'c1+0.7', '.iphone'), ('tgs_2', 'tgsessions', 'c2+1.2', '.iphone'), ('tgs_3', 'tgsessions', 'c3+2.9', '.iphone'), ('tgs_4', 'tgsessions', 'end', '.iphone'),
    ('tgd_1', 'tgdownload', 'c1+0.7', '.iphone'), ('tgd_2', 'tgdownload', 'c2+0.5', '.iphone'), ('tgd_3', 'tgdownload', 'end', '.iphone'),
    ('tgp_1', 'tgpasscode', 'c1+2.3', '.iphone'), ('tgp_2', 'tgpasscode', 'c2+0.1', '.iphone'), ('tgp_3', 'tgpasscode', 'c2+2.4', '.iphone'), ('tgp_4', 'tgpasscode', 'end', '.iphone'),
    *[(f'sum_{i}', 'summary', 'end', f'#sumgrid > .sum:nth-child({i}) .si svg') for i in range(1, 9)],
    ('bg', None, 0, None),
]

HIDE = '''#robot,#subs,#progress,#brand,#cls,#flowbar,.finger,.ripple{visibility:hidden!important}
html,body,#stage{background:transparent!important}#bg{display:none!important}
body.iconcap .card,body.iconcap .sum,body.iconcap [data-id=files] .a,body.iconcap .sum .si{background:transparent!important;border-color:transparent!important;box-shadow:none!important}'''


class Edge:
    def __init__(self):
        import websocket
        self.proc = subprocess.Popen([EDGE, '--headless=new', f'--remote-debugging-port={PORT}', '--remote-allow-origins=*', '--no-first-run',
                                      '--hide-scrollbars', '--force-device-scale-factor=1', '--window-size=1920,1080',
                                      '--allow-file-access-from-files', f'--user-data-dir={HERE / "_edge_profile"}', 'about:blank'],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        for _ in range(100):
            try:
                pages = [p for p in json.load(opener.open(f'http://127.0.0.1:{PORT}/json/list')) if p['type'] == 'page']
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
        r = self.call('Runtime.evaluate', expression=expr, returnByValue=True)
        if 'exceptionDetails' in r:
            raise RuntimeError(r['exceptionDetails'])
        return r.get('result', {}).get('value')


def trim(path, margin=6):
    """Cuts empty (transparent) edges."""
    from PIL import Image
    im = Image.open(path)
    box = im.getchannel('A').point(lambda a: 255 if a > 8 else 0).getbbox()
    if box:
        im.crop((max(0, box[0] - margin), max(0, box[1] - margin), min(im.width, box[2] + margin), min(im.height, box[3] + margin))).save(path)


edge = Edge()
edge.call('Page.navigate', url='file:///' + str(PAGE).replace('\\', '/'))
for _ in range(150):
    if edge.js("document.readyState==='complete' && document.fonts.status==='loaded' && typeof seek==='function'"):
        break
    time.sleep(0.2)
time.sleep(1.5)
edge.js('''window.tAt = (id, tok) => { const i = T.scenes.findIndex(s => s.id === id), s = T.scenes[i];
  if (tok === 'end') return s.start + s.dur - 0.8;
  const m = /^c(\\d+)([+-][\\d.]+)?$/.exec(tok); return s.start + s.lead + s.cues[+m[1]] + (+m[2] || 0); };''')
OUT.mkdir(exist_ok=True)
# the background (network + glows) once, with every slide hidden
edge.js("seek(1); document.querySelectorAll('.slide').forEach(s => s.style.visibility = 'hidden'); "
        "['#robot','#subs','#progress','#brand','#cls','#flowbar'].forEach(q => document.querySelector(q).style.visibility = 'hidden')")
data = edge.call('Page.captureScreenshot', format='png', fromSurface=True)['data']
(OUT / 'bg.png').write_bytes(base64.b64decode(data))
edge.js(f"const st = document.createElement('style'); st.textContent = {json.dumps(HIDE)}; document.head.appendChild(st);")
edge.call('Emulation.setDefaultBackgroundColorOverride', color={'r': 0, 'g': 0, 'b': 0, 'a': 0})
for name, sid, tok, sel in SHOTS:
    if sid is None:
        continue
    icon = name.split('_')[0] in ('best', 'act', 'gauge', 'sum', 'what', 'bad', 'ok')
    edge.js(f"document.body.classList.toggle('iconcap', {str(icon).lower()}); seek(tAt({json.dumps(sid)}, {json.dumps(tok)}))")
    rect = edge.js(f"""(() => {{ const sec = document.querySelector('.slide[data-id="{sid}"]');
      const e = {json.dumps(sel)} === '#robot svg' ? document.querySelector('#robot svg') : sec.querySelector({json.dumps(sel)});
      if ({json.dumps(sel)} === '#robot svg') document.getElementById('robot').style.setProperty('visibility', 'visible', 'important');
      const r = e.getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; }})()""")
    pad = 70 if name == 'robot' else 26 if sel in ('.iphone', '.vis .win') else 8 if sel == '.win' else 6
    x, y, w, h = rect[0] - pad, rect[1] - pad, rect[2] + 2 * pad, rect[3] + 2 * pad
    data = edge.call('Page.captureScreenshot', format='png', fromSurface=True, captureBeyondViewport=True,
                     clip={'x': max(0, x), 'y': max(0, y), 'width': w, 'height': h, 'scale': 2})['data']
    (OUT / f'{name}.png').write_bytes(base64.b64decode(data))
    trim(OUT / f'{name}.png')
    if name == 'robot':
        edge.js("document.getElementById('robot').style.removeProperty('visibility')")
    print(f'{name:14} {sid:11} {tok:7} {int(w)}x{int(h)}', flush=True)
print('errors:', edge.js('JSON.stringify(window.__errs||[])'))
edge.ws.close()
edge.proc.kill()
