"""PowerPoint version 2 of "Security Awareness Training_V1.2.pptx" in the look of the SAT video.

  python build_pptx.py      -> ../Security Awareness Training_V2.0.pptx

Text, cards, numbers and the classification chevrons are native (editable) PowerPoint shapes; phones, simulators and
icons are the video's own visuals (cap/, made by capture.py). Fade transitions, items appear one after another, and
every slide has the video's Khmer narration + English text in the speaker notes. Layout is drawn on the video's
1920 x 1080 grid (1 px = 6350 EMU on a 13.333 x 7.5 in slide)."""
import copy
import json
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

HERE = Path(__file__).parent
CAP = HERE / 'cap'
OUT = HERE.parent / 'Security Awareness Training_V2.0.pptx'
NARR = {n['id']: n for n in json.loads((HERE.parent / 'video' / 'narration.json').read_text(encoding='utf-8'))}
LAT, KM, KMH = 'Segoe UI', 'Khmer OS Siemreap', 'Khmer OS Battambang'
CY, CY2, TL, MUT, INK = '22D3EE', '67E8F9', '14B8A6', '9FB4D3', 'E8F1FF'
NS_P = 'http://schemas.openxmlformats.org/presentationml/2006/main'


def E(px):
    return Emu(int(round(px * 6350)))


prs = Presentation()
prs.slide_width, prs.slide_height = E(1920), E(1080)
BLANK = prs.slide_layouts[6]
SLIDES = []   # (slide, animation groups)


# ------------------------------------------------------------------ helpers
def _alpha(color_el, alpha):
    if alpha is not None:
        a = etree.SubElement(color_el, qn('a:alpha'))
        a.set('val', str(int(alpha * 1000)))


def fill(shape, hexc, alpha=None):
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor.from_string(hexc)
    _alpha(shape.fill._xPr.find(qn('a:solidFill'))[0], alpha)


def line(shape, hexc=None, alpha=None, w=1.2):
    if hexc is None:
        shape.line.fill.background()
        return
    shape.line.color.rgb = RGBColor.from_string(hexc)
    shape.line.width = Pt(w)
    _alpha(shape.line._get_or_add_ln().find(qn('a:solidFill'))[0], alpha)


def box(slide, x, y, w, h, color, alpha=None, border=None, balpha=None, radius=0.12, shape=MSO_SHAPE.ROUNDED_RECTANGLE, name=None):
    s = slide.shapes.add_shape(shape, E(x), E(y), E(w), E(h))
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    fill(s, color, alpha)
    line(s, border, balpha)
    s.shadow.inherit = False
    if name:
        s.name = name
    s.text_frame.text = ''
    return s


def text(slide, x, y, w, h, runs, size=14, color=INK, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, font=None, spacing=1.12, shape=None):
    """runs: str, or list of paragraphs, each a str or a list of (text, {color, bold, size, font})."""
    if shape is None:
        shape = slide.shapes.add_textbox(E(x), E(y), E(w), E(h))
    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    paras = runs if isinstance(runs, list) else [runs]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        for t, o in ([(para, {})] if isinstance(para, str) else para):
            r = p.add_run()
            r.text = t
            f = r.font
            f.size = Pt(o.get('size', size))
            f.bold = o.get('bold', bold)
            f.color.rgb = RGBColor.from_string(o.get('color', color))
            f.name = o.get('font', font or LAT)
            rpr = r._r.get_or_add_rPr()
            cs = etree.SubElement(rpr, qn('a:cs'))
            cs.set('typeface', o.get('km', KMH if o.get('bold', bold) else KM))
            rpr.find(qn('a:latin')).addnext(cs)
    return shape


def pic(slide, name, x, y, w=None, h=None):
    from PIL import Image
    path = CAP / f'{name}.png' if not str(name).endswith('.png') else Path(name)
    iw, ih = Image.open(path).size
    if w and not h:
        h = w * ih / iw
    elif h and not w:
        w = h * iw / ih
    return slide.shapes.add_picture(str(path), E(x), E(y), E(w), E(h))


SECS = ['សេចក្តីផ្តើម', 'ការអនុវត្តល្អ', 'ចាត់ថ្នាក់', 'Social Engineering', 'អ៊ីមែល & Telegram', 'សង្ខេប']


def new_slide(sid, phase=None, header=True):
    s = prs.slides.add_slide(BLANK)
    pic(s, 'bg', 0, 0, 1920, 1080)
    groups = []
    if header:
        sh = box(s, 120, 38, 44, 44, '0EA5E9', radius=0.3)
        text(s, 120, 38, 44, 44, [[('✓', {'bold': True, 'color': 'FFFFFF'})]], size=14, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, shape=sh)
        text(s, 178, 44, 700, 34, [[('GRC Team', {'bold': True, 'color': 'FFFFFF', 'size': 11}), ('  •  Information Security Awareness', {'color': MUT, 'size': 10.5})]], anchor=MSO_ANCHOR.MIDDLE)
        c = box(s, 1580, 42, 220, 34, '94C5FF', 4, '94C5FF', 25, radius=0.5)
        text(s, 0, 0, 0, 0, 'CLASSIFIED: INTERNAL', size=8, color='8FA3C2', align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, shape=c)
        if phase:
            x = 120
            for i, lab in enumerate(SECS):
                wpx = 52 + len(lab) * (8 if lab.isascii() else 11)
                cur, done = i + 1 == phase, i + 1 < phase
                b = box(s, x, 104, wpx, 34, CY if cur else ('10B981' if done else 'FFFFFF'), None if cur else (12 if done else 4),
                        CY2 if cur else ('10B981' if done else 'FFFFFF'), None if cur else (35 if done else 8), radius=0.5)
                text(s, 0, 0, 0, 0, [[(('✓ ' if done else f'{i + 1}  ') + lab, {'color': '03222B' if cur else ('A7F3D0' if done else '7086A6'), 'bold': cur, 'size': 9})]],
                     align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, shape=b)
                x += wpx + 12
        n = len(prs.slides._sldIdLst)
        text(s, 1700, 1032, 100, 30, f'{n:02d}', size=10, color='5F7596', align=PP_ALIGN.RIGHT)
    n = NARR.get(sid)
    if n:
        s.notes_slide.notes_text_frame.text = n['say'] + '\n\n— English —\n' + n['sub']
    SLIDES.append((s, groups, sid))
    return s, groups


CHIP = {'cy': (CY, '03222B'), 'red': ('DC2626', 'FFFFFF'), 'vio': ('7C3AED', 'FFFFFF'), 'tg': ('229ED9', 'FFFFFF')}


def chip(s, x, y, label, kind='cy'):
    bg, fg = CHIP[kind]
    w = 48 + sum(12 if ord(c) > 0x1000 else 10.5 for c in label)
    b = box(s, x, y, w, 40, bg, radius=0.5)
    text(s, 0, 0, 0, 0, [[(label, {'color': fg, 'bold': True, 'size': 10})]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, shape=b)
    return b


def title(s, x, y, w, parts, size=30):
    return text(s, x, y, w, 90, [[(t, {'color': c, 'bold': True, 'size': size}) for t, c in parts]], spacing=1.0)


def row(s, x, y, w, badge, main, small, bad=False, h=88):
    """A list row like the video: badge square + Khmer line (bold parts in cyan) + small English line."""
    b = box(s, x, y, w, h, '94C5FF', 7, '94C5FF', 16, radius=0.2)
    k = box(s, x + 18, y + (h - 48) / 2, 48, 48, 'DC2626' if bad else CY, radius=0.28)
    text(s, 0, 0, 0, 0, [[(badge, {'color': 'FFFFFF' if bad else '03222B', 'bold': True, 'size': 12})]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, shape=k)
    runs = [(t, {'color': CY2, 'bold': True} if i % 2 else {}) for i, t in enumerate(main.split('*'))]
    t = text(s, x + 84, y + 10, w - 100, h - 20, [runs, [(small, {'size': 9.5, 'color': MUT})]], size=14, anchor=MSO_ANCHOR.MIDDLE, spacing=1.05)
    return [b, k, t]


def card(s, x, y, w, h, color='94C5FF', alpha=7, border='94C5FF', balpha=16, radius=0.08):
    return box(s, x, y, w, h, color, alpha, border, balpha, radius=radius)


# ------------------------------------------------------------------ slides
# 1 title
s, g = new_slide('intro', header=False)
g.append([pic(s, 'robot', 170, 200, h=700)])
g.append([chip(s, 900, 190, 'GRC TRAINING • v2.0')])
g.append([text(s, 900, 250, 960, 190, [[('Information Security', {'bold': True, 'size': 34, 'color': 'FFFFFF'})], [('Awareness Training', {'bold': True, 'size': 34, 'color': CY2})]], spacing=1.0)])
g.append([text(s, 900, 440, 960, 60, [[('វគ្គបណ្តុះបណ្តាល ការយល់ដឹងអំពីសន្តិសុខព័ត៌មាន', {'bold': True, 'size': 20, 'color': 'FFFFFF'})]])])
g.append([text(s, 900, 505, 960, 40, [[('Protecting Our Digital Workplace', {'size': 15, 'color': CY2})]])])
p1 = box(s, 900, 565, 150, 38, CY, 12, CY2, 35, radius=0.5); text(s, 0, 0, 0, 0, [[('PRESENTED BY', {'size': 8.5, 'bold': True, 'color': CY2})]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, shape=p1)
p2 = box(s, 1062, 565, 420, 38, 'FFFFFF', 6, '94C5FF', 16, radius=0.5); text(s, 0, 0, 0, 0, [[('Governance, Risk & Compliance Team', {'size': 9.5, 'bold': True, 'color': 'FFFFFF'})]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, shape=p2)
g.append([p1, p2])
g.append([pic(s, 'intro_shield', 900, 640, w=560)])
c = box(s, 1580, 42, 220, 34, '94C5FF', 4, '94C5FF', 25, radius=0.5)
text(s, 0, 0, 0, 0, 'CLASSIFIED: INTERNAL', size=8, color='8FA3C2', align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, shape=c)

# 2 agenda
s, g = new_slide('agenda')
g.append([chip(s, 120, 190, 'មាតិកា • TABLE OF CONTENTS'), title(s, 120, 250, 1600, [('អ្វីដែលយើងនឹង', 'FFFFFF'), ('សិក្សា', CY2)])])
AG = [('សេចក្តីផ្តើម និងមូលហេតុ', 'Introduction & Why It Matters'), ('ការអនុវត្តល្អបំផុត', 'Best Practice for Cyber Security'), ('ការចាត់ថ្នាក់ព័ត៌មាន', 'Information Classification'),
      ('Social Engineering', 'Phishing & human tricks'), ('អ៊ីមែល និង Telegram', 'Email & Telegram Security Guidelines'), ('សង្ខេប និងកម្រងសំណួរ', 'Summary & Quiz')]
for i, (km, en) in enumerate(AG):
    x, y = 120 + (i % 3) * 568, 420 + (i // 3) * 250
    c = card(s, x, y, 544, 226)
    t = text(s, x + 30, y + 22, 490, 190, [[(f'0{i + 1}', {'size': 30, 'bold': True, 'color': '3E8FA6'})], [(km, {'size': 17, 'bold': True, 'color': 'FFFFFF'})], [(en, {'size': 10.5, 'color': MUT})]], spacing=1.1)
    g.append([c, t])

# 3 what
s, g = new_slide('what', 1)
g.append([chip(s, 120, 190, 'សេចក្តីផ្តើម • INTRODUCTION'), title(s, 120, 250, 1600, [('តើ', 'FFFFFF'), ('វគ្គបណ្តុះបណ្តាលនេះ', CY2), (' ជាអ្វី?', 'FFFFFF')]),
          text(s, 120, 345, 1600, 40, [[('What is Information Security Awareness Training? — Educational program to spot threats, secure data, and build safe digital habits.', {'size': 13, 'color': CY2})]])])
for i, (icon, km, en) in enumerate([('what_radar', 'សម្គាល់ការគំរាមកំហែង', 'Spot threats'), ('what_data', 'ការពារទិន្នន័យ', 'Secure data'), ('what_habit', 'ទម្លាប់ឌីជីថលដែលមានសុវត្ថិភាព', 'Build safe digital habits')]):
    x = 120 + i * 568
    c = card(s, x, 450, 544, 400)
    p = pic(s, icon, x + 197, 490, w=150)
    t = text(s, x + 20, 680, 504, 140, [[(km, {'bold': True, 'size': 17, 'color': 'FFFFFF'})], [(en, {'size': 12, 'color': CY2})]], align=PP_ALIGN.CENTER)
    g.append([c, p, t])

# 4 why
s, g = new_slide('why', 1)
g.append([chip(s, 120, 190, 'ហេតុអ្វីសំខាន់ • WHY IT MATTERS'), title(s, 120, 250, 1600, [('មូលហេតុ', 'FFFFFF'), ('ចំនួនបួន', CY2)])])
WHY = [('22D3EE', 'កាត់បន្ថយកំហុសមនុស្ស និងការវាយប្រហារ', 'Reduce human error & cyber attacks — help employees avoid phishing, scams and security mistakes'),
       ('10B981', 'កសាងវប្បធម៌សន្តិសុខ', "Build security culture — cybersecurity is everyone's responsibility"),
       ('F59E0B', 'ការពារទ្រព្យសម្បត្តិ', 'Protect assets — prevent leaks of data/information and maintain client trust'),
       ('8B5CF6', 'បំពេញតម្រូវការអនុលោមភាព', 'Meet compliance requirements — ISO and PCI DSS standards')]
for i, (col, km, en) in enumerate(WHY):
    x, y = 120 + (i % 2) * 852, 400 + (i // 2) * 250
    c = card(s, x, y, 828, 226)
    n = text(s, x + 30, y + 40, 150, 140, [[(f'0{i + 1}', {'bold': True, 'size': 44, 'color': col})]], anchor=MSO_ANCHOR.MIDDLE)
    t = text(s, x + 190, y + 30, 610, 170, [[(km, {'bold': True, 'size': 17, 'color': 'FFFFFF'})], [(en, {'size': 11, 'color': MUT})]], anchor=MSO_ANCHOR.MIDDLE)
    g.append([c, n, t])

# 5 best
s, g = new_slide('best', 2)
g.append([chip(s, 120, 190, 'ការអនុវត្តល្អបំផុត • BEST PRACTICE'), title(s, 120, 250, 1600, [('ចំណុចខ្សោយ', 'FFFFFF'), ('ទូទៅ ៤', CY2)]),
          text(s, 120, 345, 1000, 40, [[('Common security weaknesses', {'size': 13, 'color': CY2})]])])
BEST = [('10B981', 'A7F3D0', 'សន្តិសុខពាក្យសម្ងាត់', 'Password Security'), ('3B82F6', 'BFDBFE', 'សុវត្ថិភាពអ៊ីនធឺណិត', 'Internet Safety'),
        ('F59E0B', 'FDE68A', 'តុស្អាត និងអេក្រង់ស្អាត', 'Clear Desk & Clear Screen'), ('8B5CF6', 'DDD6FE', 'ឧបករណ៍ផ្ទាល់ខ្លួន', 'Bring Your Own Device (BYOD)')]
for i, (col, light, km, en) in enumerate(BEST):
    x = 120 + i * 424
    c = card(s, x, 440, 400, 400, col, 18, col, 45)
    tg = box(s, x + 26, 466, 66, 34, col, radius=0.5); text(s, 0, 0, 0, 0, [[(f'{i + 1}/4', {'bold': True, 'size': 10, 'color': 'FFFFFF'})]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, shape=tg)
    p = pic(s, f'best_{i + 1}', x + 26, 530, w=110)
    t = text(s, x + 26, 670, 350, 150, [[(km, {'bold': True, 'size': 17, 'color': 'FFFFFF'})], [(en, {'size': 11, 'color': light})]])
    g.append([c, tg, p, t])

# 6 password
s, g = new_slide('password', 2)
g.append([chip(s, 120, 190, '1/4 • PASSWORD SECURITY'), title(s, 120, 250, 1000, [('សន្តិសុខ', 'FFFFFF'), ('ពាក្យសម្ងាត់', CY2)])])
for i, (b, m, sm, bad) in enumerate([('✓', 'កុំចែករំលែក • ប្តូរជាប្រចាំ • បើក *2FA*', 'Never share • change regularly • enable 2FA', False),
                                       ('12+', 'យ៉ាងតិច *12 តួអក្សរ* កាន់តែវែងកាន់តែល្អ', 'Length: at least 12 characters, the longer the better', False),
                                       ('Aa', 'អក្សរធំ • តូច • លេខ • *សញ្ញាពិសេស*', 'Complexity: upper & lower case, numbers, special symbols', False),
                                       ('1:1', 'មួយគណនី *មួយពាក្យសម្ងាត់*', 'Uniqueness: a different password for each account', False),
                                       ('✕', 'កុំប្រើ *ថ្ងៃកំណើត ឈ្មោះសត្វ អាសយដ្ឋាន*', 'Avoid personal information', True)]):
    g.append(row(s, 120, 360 + i * 104, 940, b, m, sm, bad))
g.append([pic(s, 'pw_window', 1120, 360, w=680)])

# 7 crack
s, g = new_slide('crack', 2)
g.append([chip(s, 120, 190, '1/4 • PASSWORD STRUCTURES'), title(s, 120, 250, 1600, [('រយៈពេល', 'FFFFFF'), ('បំបែកពាក្យសម្ងាត់', CY2)]),
          text(s, 120, 345, 600, 40, [[('Time to crack', {'size': 13, 'color': CY2})]])])
for i, (col, light, km, ex, tm) in enumerate([('EF4444', 'FCA5A5', 'ខ្សោយខ្លាំង • Very Weak', 'qwerty · password · 123456 · iloveyou', 'Seconds → Minutes'),
                                                ('F59E0B', 'FDE68A', 'ល្អ • Good', 'qwerty916QWE · PassW0rd1934B', 'Months → Years'),
                                                ('10B981', 'A7F3D0', 'ខ្លាំង • Strong', '3d93_0F@!_t0m012RoW · b1AcK_5h33P!3$@1', 'Centuries')]):
    x = 120 + i * 568
    c = card(s, x, 420, 544, 470, '94C5FF', 7, col, 45)
    p = pic(s, f'gauge_{i + 1}', x + 122, 455, w=300)
    t = text(s, x + 20, 650, 504, 120, [[(km, {'bold': True, 'size': 17, 'color': light})], [(ex, {'size': 10.5, 'color': 'FFFFFF', 'font': 'Consolas'})]], align=PP_ALIGN.CENTER)
    tg = box(s, x + 122, 800, 300, 46, col, radius=0.5); text(s, 0, 0, 0, 0, [[(tm, {'bold': True, 'size': 10.5, 'color': 'FFFFFF'})]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, shape=tg)
    g.append([c, p, t, tg])

# 8 internet
s, g = new_slide('internet', 2)
g.append([chip(s, 120, 190, '2/4 • INTERNET SAFETY'), title(s, 120, 250, 1000, [('សុវត្ថិភាព', 'FFFFFF'), ('អ៊ីនធឺណិត', CY2)])])
g.append([pic(s, 'net', 1130, 180, h=780)])
for i, (b, m, sm) in enumerate([('✓', 'ពិនិត្យ *https://* ជានិច្ច', 'Always ensure websites start with https'),
                                 ('!', 'កុំចែករំលែកព័ត៌មានរសើប លើ*វេទិកាសាធារណៈ*', 'Avoid sharing sensitive information in public platforms'),
                                 ('↓', 'ទាញយកតែពី*ប្រភពទុកចិត្ត* • កុំចុច Ads មិនស្គាល់', 'Only download from trusted sources • avoid unknown ads')]):
    g.append(row(s, 120, 360 + i * 104, 940, b, m, sm))
q = box(s, 120, 690, 940, 150, CY, 7, None, radius=0.08)
text(s, 0, 0, 0, 0, [[('“យើងត្រូវតែត្រឹមត្រូវរាល់ពេល ប៉ុន្តែអ្នកវាយប្រហារ ត្រូវការត្រឹមត្រូវតែម្តង”', {'size': 14, 'color': 'FFFFFF'})],
                     [('“You have to be right all the time, but attackers only need one time right to compromise yours.”', {'size': 10, 'color': MUT})]], anchor=MSO_ANCHOR.MIDDLE, shape=q)
q.text_frame.margin_left = E(30)
g.append([q])

# 9 desk
s, g = new_slide('desk', 2)
g.append([chip(s, 120, 190, '3/4 • CLEAR DESK & CLEAR SCREEN'), title(s, 120, 250, 1000, [('តុស្អាត និង', 'FFFFFF'), ('អេក្រង់ស្អាត', CY2)])])
for i, (b, m, sm, bad) in enumerate([('1', 'ចាក់សោអេក្រង់ *Win + L* ពេលចាកចេញ', 'Lock computers whenever leaving your desk', False),
                                       ('2', 'ឯកសាររសើប និង *USB* ក្នុងទូជាប់សោ', 'Secure storage: lock files and USB drives in drawers/cabinets', False),
                                       ('3', 'លុប*ក្តារខៀន* ក្រោយប្រជុំ', 'Clean meeting rooms: erase whiteboards, clear notes', False),
                                       ('4', 'យក*ឯកសារបោះពុម្ព*ភ្លាមៗ', 'Printer safety: pick up printed documents immediately', False),
                                       ('✕', '*កុំ*សរសេរពាក្យសម្ងាត់លើក្រដាសស្អិត!', 'No sticky notes: NEVER write passwords on paper', True)]):
    g.append(row(s, 120, 360 + i * 104, 940, b, m, sm, bad))
g.append([pic(s, 'desk', 1150, 300, w=640)])

# 10 byod
s, g = new_slide('byod', 2)
g.append([chip(s, 120, 190, '4/4 • BRING YOUR OWN DEVICE'), title(s, 120, 250, 1000, [('ឧបករណ៍', 'FFFFFF'), ('ផ្ទាល់ខ្លួន', CY2)])])
for i, (b, m, sm, bad) in enumerate([('1', '*Firewall • Antivirus • EDR*', 'Security tools: install the required tools', False),
                                       ('2', 'ធ្វើ*បច្ចុប្បន្នភាព* OS និងកម្មវិធី', 'Keep updated: update OS and applications regularly', False),
                                       ('3', '*MFA* ជានិច្ច ពេលចូលប្រព័ន្ធក្រុមហ៊ុន', "MFA is always required for company resources", False),
                                       ('4', '*អ៊ិនគ្រីប* ទិន្នន័យ ពេលរក្សាទុក និងបញ្ជូន', 'Encrypt data at rest and in transit', False),
                                       ('!', 'បាត់ឧបករណ៍? ហៅ *IT Helpdesk* ភ្លាម', 'Report loss immediately', True)]):
    g.append(row(s, 120, 360 + i * 104, 940, b, m, sm, bad))
g.append([pic(s, 'byod', 1150, 300, w=640)])

# 11 classify (native chevrons)
s, g = new_slide('classify', 3)
g.append([chip(s, 120, 190, 'ការចាត់ថ្នាក់ • INFORMATION CLASSIFICATION'), title(s, 120, 250, 1600, [('ព័ត៌មាន', 'FFFFFF'), ('បួនកម្រិត', CY2)])])
TIERS = [('16A34A', '4ADE80', 'LOW', 'PUBLIC', 'សាធារណៈ', ['ផលិតផល & ការផ្សព្វផ្សាយ', 'ព័ត៌មានទូទៅ • News']),
         ('2563EB', '60A5FA', 'MEDIUM', 'INTERNAL', 'ផ្ទៃក្នុង', ['ព្រឹត្តិបត្រ • Newsletters', 'គំរូឯកសារ • Form templates']),
         ('D97706', 'FBBF24', 'HIGH', 'CONFIDENTIAL', 'សម្ងាត់', ['ព័ត៌មានវេជ្ជសាស្ត្រ', 'តាមនាយកដ្ឋាន • ប្រាក់ខែបុគ្គលិក']),
         ('DC2626', 'F87171', 'CRITICAL', 'RESTRICTED', 'ហាមឃាត់', ['License / Product key', 'ប្រាក់ចំណេញ • ផែនការអាជីវកម្ម'])]
for i, (col, light, lvl, en, km, exs) in enumerate(TIERS):
    x = 120 + i * 400
    l = text(s, x, 380, 360, 40, [[(lvl, {'bold': True, 'size': 13, 'color': light})]], align=PP_ALIGN.CENTER)
    ch = s.shapes.add_shape(MSO_SHAPE.CHEVRON, E(x), E(425), E(360), E(90)); fill(ch, col); line(ch); ch.shadow.inherit = False
    text(s, 0, 0, 0, 0, [[(en, {'bold': True, 'size': 14, 'color': 'FFFFFF'})]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, shape=ch)
    k = text(s, x, 530, 360, 40, [[(km, {'bold': True, 'size': 15, 'color': 'FFFFFF'})]], align=PP_ALIGN.CENTER)
    items = [l, ch, k]
    for j, ex in enumerate(exs):
        e = box(s, x + 20, 590 + j * 70, 320, 58, col, 22, None, radius=0.2)
        text(s, 0, 0, 0, 0, [[(ex, {'bold': True, 'size': 11, 'color': 'FFFFFF'})]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, shape=e)
        items.append(e)
    g.append(items)
ar = s.shapes.add_shape(MSO_SHAPE.PENTAGON, E(120), E(800), E(1540), E(56)); line(ar); ar.shadow.inherit = False
ar.fill.gradient(); ar.fill.gradient_angle = 0
st = ar.fill.gradient_stops
st[0].color.rgb, st[0].position = RGBColor.from_string('16A34A'), 0
st[1].color.rgb, st[1].position = RGBColor.from_string('DC2626'), 1.0
text(s, 0, 0, 0, 0, [[('INCREASING DATA SENSITIVITY →', {'bold': True, 'size': 11, 'color': 'FFFFFF'})]], anchor=MSO_ANCHOR.MIDDLE, shape=ar)
ar.text_frame.margin_left = E(30)
g.append([ar])

# 12 phishing
s, g = new_slide('phishing', 4)
g.append([chip(s, 120, 190, 'SOCIAL ENGINEERING', 'red'), title(s, 120, 250, 1000, [('តើ ', 'FFFFFF'), ('Phishing', CY2), (' ជាអ្វី?', 'FFFFFF')])])
for i, (b, m, sm, bad) in enumerate([('1', 'ការបោកប្រាស់តាម *អ៊ីមែល • SMS • ទូរស័ព្ទ*', 'A type of online scam via email, SMS, phone calls', False),
                                       ('!', 'លួច*គណនី និងព័ត៌មានរសើប*', 'Purpose: stealing credentials & sensitive information', True),
                                       ('!', 'ដំឡើង*មេរោគ និង Ransomware*', 'Purpose: malware & ransomware installation', True),
                                       ('2', 'ចុច*តំណភ្ជាប់* • ទាញយក*ឯកសារភ្ជាប់*', 'Techniques: clicking links & entering info, downloading attachments', False)]):
    g.append(row(s, 120, 360 + i * 104, 940, b, m, sm, bad))
g.append([pic(s, 'phish_phone', 1240, 90, h=900)])

# 13 checks
s, g = new_slide('checks', 4)
g.append([chip(s, 120, 170, 'PHISHING AWARENESS • EMAIL SAFETY', 'red'), title(s, 120, 222, 1600, [('សម្គាល់', 'FFFFFF'), ('អ៊ីមែល Phishing', CY2)], size=26)])
g.append([pic(s, 'phish_email', 110, 300, w=880)])
for i, (m, sm) in enumerate([('ប្រធានបទ *បន្ទាន់ និងគួរភ័យ*', 'Urgency and alarm subject'), ('អ៊ីមែល*ក្លែងក្លាយ* .con ≠ .com', 'Fake email address'), ('*តំណភ្ជាប់ Phishing*', 'Phishing link to a fake site')]):
    g.append(row(s, 1030, 300 + i * 100, 680, str(i + 1), m, sm, True))
c = card(s, 1030, 620, 680, 150, 'EF4444', 10, 'EF4444', 50)
n80 = text(s, 1060, 640, 220, 110, [[('80%', {'bold': True, 'size': 40, 'color': 'F87171'})]], anchor=MSO_ANCHOR.MIDDLE)
t = text(s, 1270, 640, 420, 110, [[('អាចជា ', {'size': 14}), ('Phishing', {'bold': True, 'size': 14, 'color': 'FCA5A5'})], [('could be a phishing email', {'size': 10, 'color': MUT})]], anchor=MSO_ANCHOR.MIDDLE)
g.append([c, n80, t])
t2 = text(s, 1030, 800, 680, 120, [[('✓ ផ្ទៀងផ្ទាត់អ្នកផ្ញើ  ✓ ប្រុងប្រយ័ត្នពាក្យបន្ទាន់  ✓ កុំចុចតំណ/ឯកសារសង្ស័យ  ✓ ពិនិត្យវេយ្យាករណ៍', {'size': 11.5, 'color': 'A7F3D0'})],
                                    [('Verify sender • beware urgency • no suspicious links • check grammar', {'size': 9.5, 'color': MUT})]])
g.append([t2])

# 14 email
s, g = new_slide('email', 5)
g.append([chip(s, 120, 190, 'EMAIL SECURITY', 'vio'), title(s, 120, 250, 1600, [('ពេលទទួល', 'FFFFFF'), ('អ៊ីមែលគួរឱ្យសង្ស័យ', CY2)])])
g.append([text(s, 120, 350, 1600, 110, [[('សន្តិសុខអ៊ីមែល៖ ការពារគណនីអ៊ីមែល ការទំនាក់ទំនង និងទិន្នន័យ ពីការចូលប្រើដោយគ្មានការអនុញ្ញាត Phishing មេរោគ និងការបោកប្រាស់', {'size': 14, 'color': 'CFE0FF'})],
                                     [('Email security is protecting email accounts, communication and data from unauthorized access, phishing, malware, scams and other cyber threats.', {'size': 10, 'color': MUT})]])])
for i, (km, en, col, light) in enumerate([('កុំចុច', 'DO NOT CLICK', 'EF4444', 'FCA5A5'), ('កុំបញ្ជូនបន្ត', 'DO NOT FORWARD', 'EF4444', 'FCA5A5'), ('រាយការណ៍', 'REPORT IT', '10B981', '6EE7B7'), ('លុបចោល', 'DELETE IT', '10B981', '6EE7B7')]):
    x = 120 + i * 424
    c = card(s, x, 520, 400, 340, '94C5FF', 7, col, 50)
    p = pic(s, f'act_{i + 1}', x + 140, 555, w=120)
    t = text(s, x + 20, 710, 360, 120, [[(km, {'bold': True, 'size': 17, 'color': 'FFFFFF'})], [(en, {'bold': True, 'size': 12, 'color': light})]], align=PP_ALIGN.CENTER)
    g.append([c, p, t])

# 15 files
s, g = new_slide('files', 5)
g.append([chip(s, 120, 190, 'HIGH-RISK ATTACHMENTS', 'red'), title(s, 120, 250, 1600, [('ឯកសារភ្ជាប់', 'FFFFFF'), ('ហានិភ័យខ្ពស់', CY2)])])
c = card(s, 120, 370, 1580, 270, 'EF4444', 10, 'EF4444', 50)
t = text(s, 160, 395, 1400, 50, [[('⛔ កុំបើកជាដាច់ខាត  ', {'bold': True, 'size': 16, 'color': 'FCA5A5'}), ('DO NOT OPEN — .exe | .bat | .vbs | .html | .scr', {'bold': True, 'size': 11, 'color': 'FCA5A5'})]])
g.append([c, t, pic(s, 'bad_files', 160, 460, h=150)])
c = card(s, 120, 670, 1580, 270, 'F59E0B', 8, 'F59E0B', 45)
t = text(s, 160, 695, 1400, 50, [[('🔎 ហានិភ័យទាបជាង — ត្រូវផ្ទៀងផ្ទាត់ប្រភពសិន  ', {'bold': True, 'size': 16, 'color': 'FDE68A'}), ('VERIFY THE SOURCE', {'bold': True, 'size': 11, 'color': 'FDE68A'})]])
g.append([c, t, pic(s, 'ok_files', 160, 760, h=150)])

# 16 telegram overview
s, g = new_slide('telegram', 5)
g.append([chip(s, 120, 190, 'TELEGRAM SECURITY GUIDELINE', 'tg'), title(s, 120, 250, 1000, [('ការពារគណនី', 'FFFFFF'), (' Telegram', CY2)])])
for i, (m, sm) in enumerate([('បើក *Two-Step Verification*', 'Enable 2-factor authentication'), ('ពិនិត្យ*ឧបករណ៍សង្ស័យ* និងបញ្ចប់វគ្គ', 'Check suspicious devices & terminate sessions'),
                             ('បិទ*ទាញយកស្វ័យប្រវត្តិ*', 'Disable auto file download'), ('បើក *Local Passcode*', 'Turn on local passcode')]):
    g.append(row(s, 120, 360 + i * 104, 940, str(i + 1), m, sm))
g.append([pic(s, 'tg_overview', 1240, 90, h=900)])


# 17-20 Telegram steps: phones in a row with step labels (like the original strips)
def steps(sid, chip_label, ttl, shots):
    s, g = new_slide(sid, 5)
    g.append([chip(s, 120, 170, chip_label, 'tg'), title(s, 120, 222, 1700, ttl, size=26)])
    n = len(shots)
    ph = 640 if n <= 4 else 600
    pw = ph * 479 / 946
    gap = (1680 - n * pw) / max(1, n - 1) if n > 1 else 0
    gap = min(gap, 80)
    x0 = 120 + (1680 - (n * pw + (n - 1) * gap)) / 2
    for i, (img, km, en) in enumerate(shots):
        x = x0 + i * (pw + gap)
        b = box(s, x + pw / 2 - 22, 310, 44, 44, CY, radius=0.5)
        text(s, 0, 0, 0, 0, [[(str(i + 1), {'bold': True, 'size': 13, 'color': '03222B'})]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, shape=b)
        lb = text(s, x - 20, 362, pw + 40, 70, [[(km, {'bold': True, 'size': 11.5, 'color': 'FFFFFF'})], [(en, {'size': 9, 'color': CY2})]], align=PP_ALIGN.CENTER, spacing=1.0)
        p = pic(s, img, x, 440, h=ph - 30)
        g.append([b, lb, p])


steps('tg2fa', 'TELEGRAM • 1/4', [('បើក', 'FFFFFF'), (' Two-Step Verification', CY2)],
      [('tg2fa_1', 'ចូល Settings', 'Settings'), ('tg2fa_2', 'Two-Step Verification', 'Privacy and Security'), ('tg2fa_3', 'វាយពាក្យសម្ងាត់ ២ដង', 'Create password'),
       ('tg2fa_4', 'អ៊ីមែលសង្គ្រោះ', 'Recovery email'), ('tg2fa_5', 'រួចរាល់!', 'Password set')])
steps('tgsessions', 'TELEGRAM • 2/4', [('ពិនិត្យ', 'FFFFFF'), ('ឧបករណ៍សង្ស័យ', CY2)],
      [('tgs_1', 'ចូល Settings', 'Settings'), ('tgs_2', 'Devices • រកឧបករណ៍មិនស្គាល់', 'Find unknown devices'), ('tgs_3', 'Terminate All Other Sessions', 'Confirm'),
       ('tgs_4', 'បញ្ចប់វគ្គផ្សេងទាំងអស់', 'Only this device remains')])
steps('tgdownload', 'TELEGRAM • 3/4', [('បិទ', 'FFFFFF'), ('ទាញយកស្វ័យប្រវត្តិ', CY2)],
      [('tgd_1', 'ចូល Settings', 'Settings'), ('tgd_2', 'Data and Storage', 'Automatic Media Download'), ('tgd_3', 'បិទ Photos • Videos • Files', 'All off')])
steps('tgpasscode', 'TELEGRAM • 4/4', [('បើក', 'FFFFFF'), (' Local Passcode', CY2)],
      [('tgp_1', 'Privacy and Security', 'Settings → Privacy'), ('tgp_2', 'Turn Passcode On', 'Passcode & Face ID'), ('tgp_3', 'វាយលេខកូដ ២ដង', 'Enter passcode twice'),
       ('tgp_4', 'Passcode បានបើក', 'Auto-Lock • Face ID')])

# 21 summary
s, g = new_slide('summary', 6)
g.append([chip(s, 120, 190, 'សង្ខេប • SUMMARY'), title(s, 120, 250, 1600, [('ចងចាំ', 'FFFFFF'), (' ៨ ចំណុចសំខាន់', CY2)])])
SUM = [('047857', 'Password Security', '12+ តួអក្សរ ខុសគ្នាគ្រប់គណនី 2FA'), ('1D4ED8', 'Internet Safety', 'HTTPS តែប៉ុណ្ណោះ • គ្មានព័ត៌មានរសើបលើវេទិកាសាធារណៈ'),
       ('047857', 'Clear Desk & Screen', 'ចាក់សោអេក្រង់ • រក្សាឯកសារពេលចាកចេញ'), ('1D4ED8', 'BYOD', 'ធ្វើបច្ចុប្បន្នភាព • រាយការណ៍ពេលបាត់'),
       ('1D4ED8', 'Info Classification', 'សាធារណៈ • ផ្ទៃក្នុង • សម្ងាត់ • ហាមឃាត់'), ('047857', 'Social Engineering', 'ឈប់គិតមុនចុច • ផ្ទៀងផ្ទាត់ • រាយការណ៍'),
       ('1D4ED8', 'Email & Telegram', 'MFA • ពិនិត្យវគ្គ • កុំទុកចិត្តឯកសារភ្ជាប់'), ('047857', 'Compliance', 'ការពារទំនុកចិត្តអតិថិជន និងអាជីវកម្ម')]
for i, (col, h, p) in enumerate(SUM):
    x, y = 120 + (i % 4) * 400, 380 + (i // 4) * 280
    c = box(s, x, y, 380, 256, col, radius=0.08)
    ic = box(s, x + 22, y + 22, 52, 52, 'FFFFFF', 15, None, radius=0.28)
    im = pic(s, f'sum_{i + 1}', x + 33, y + 33, w=30)
    t = text(s, x + 22, y + 92, 340, 150, [[(h, {'bold': True, 'size': 13.5, 'color': 'FFFFFF'})], [(p, {'size': 12, 'color': 'EEF5FF'})]], spacing=1.1)
    g.append([c, ic, im, t])

# 22 quiz
s, g = new_slide('quiz', 6)
qb = box(s, 200, 250, 500, 500, 'FFFFFF', radius=0.08)
g.append([qb, pic(s, HERE.parent / 'video' / 'img' / 'quiz_qr.png', 230, 280, w=440)])
g.append([text(s, 820, 260, 1000, 300, [[('Quiz!', {'bold': True, 'size': 110, 'color': CY2})]])])
g.append([text(s, 820, 560, 1000, 160, [[('ស្កេន QR ដើម្បីធ្វើកម្រងសំណួរ', {'bold': True, 'size': 22, 'color': 'FFFFFF'})], [('Scan to take the quiz — good luck!', {'size': 14, 'color': CY2})]])])

# 23 thank you
s, g = new_slide('outro')
g.append([text(s, 120, 190, 1100, 160, [[('អរគុណ! ', {'bold': True, 'size': 46, 'color': 'FFFFFF'}), ('Thank You!', {'bold': True, 'size': 36, 'color': CY2})]])])
g.append([text(s, 120, 360, 1050, 110, [[('សូមទាក់ទងក្រុម GRC សម្រាប់សំណួរ ឬការពន្យល់បន្ថែម', {'size': 16})], [('We welcome any questions or requests for further clarification.', {'size': 11, 'color': MUT})]])])
for i, (ph_, em) in enumerate([('+855 93 222 724', 'sambath.nhek@gcx.com.kh'), ('+855 87 222 045', 'leakhna.sorn@gcx.com.kh')]):
    c = card(s, 120, 500 + i * 110, 1000, 90, radius=0.2)
    text(s, 0, 0, 0, 0, [[('☎  ' + ph_ + '     ✉  ' + em, {'size': 14, 'color': 'FFFFFF'})]], anchor=MSO_ANCHOR.MIDDLE, shape=c)
    c.text_frame.margin_left = E(30)
    g.append([c])
tg = box(s, 120, 760, 620, 56, '10B981', 14, '10B981', 40, radius=0.5)
text(s, 0, 0, 0, 0, [[("🛡 Security is everyone's responsibility", {'bold': True, 'size': 13, 'color': 'A7F3D0'})]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, shape=tg)
g.append([tg])
g.append([pic(s, 'robot', 1260, 170, h=780)])


# ------------------------------------------------------------------ transitions + entrance animations (fade, one after another)
def timing_xml(groups):
    ids = iter(range(3, 10000))
    pars = []
    for k, grp in enumerate(groups):
        delay = 250 + k * 380
        effects = []
        for shp in grp:
            sp = shp.shape_id
            c1, c2, c3 = next(ids), next(ids), next(ids)
            effects.append(f'<p:par><p:cTn id="{c1}" presetID="10" presetClass="entr" presetSubtype="0" fill="hold" nodeType="withEffect"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>'
                           f'<p:set><p:cBhvr><p:cTn id="{c2}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn><p:tgtEl><p:spTgt spid="{sp}"/></p:tgtEl>'
                           f'<p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr><p:to><p:strVal val="visible"/></p:to></p:set>'
                           f'<p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="{c3}" dur="500"/><p:tgtEl><p:spTgt spid="{sp}"/></p:tgtEl></p:cBhvr></p:animEffect>'
                           f'</p:childTnLst></p:cTn></p:par>')
        pars.append(f'<p:par><p:cTn id="{next(ids)}" fill="hold"><p:stCondLst><p:cond delay="{delay}"/></p:stCondLst><p:childTnLst>{"".join(effects)}</p:childTnLst></p:cTn></p:par>')
    return (f'<p:timing xmlns:p="{NS_P}"><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>'
            f'<p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>'
            f'<p:par><p:cTn id="{next(ids)}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/><p:cond evt="onBegin" delay="0"><p:tn val="2"/></p:cond></p:stCondLst>'
            f'<p:childTnLst>{"".join(pars)}</p:childTnLst></p:cTn></p:par>'
            f'</p:childTnLst></p:cTn><p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
            f'<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq>'
            f'</p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>')


for slide, groups, sid in SLIDES:
    root = slide._element
    trans = etree.fromstring(f'<p:transition xmlns:p="{NS_P}" spd="med">' + ('<p:push dir="l"/>' if sid.startswith('tg') else '<p:fade/>') + '</p:transition>')
    root.find(qn('p:clrMapOvr')).addnext(trans)
    groups = [grp for grp in groups if grp]
    if groups:
        trans.addnext(etree.fromstring(timing_xml(groups)))

prs.core_properties.title = 'Information Security Awareness Training v2.0'
prs.core_properties.author = 'GRC Team'
prs.save(OUT)
print(OUT, len(prs.slides), 'slides')
