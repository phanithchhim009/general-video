"""Copies the real customer-app screens (mock build, 12 Nov 2026) and paints over the mock-only "(demo)" buttons."""
import shutil
from pathlib import Path
from PIL import Image, ImageDraw

SRC = Path(r'E:\temp\claude\cd4f39a174ed22f7\e1c502c2-48b1-47b1-ac0a-ecbccb595766\scratchpad\allpages\shots\customer')
OUT = Path(__file__).parent / 'screens'
OUT.mkdir(exist_ok=True)
NAMES = {'02_Intro': 'intro', '03_Permission__location': 'perm_loc', '04_Permission__notifications': 'perm_notif',
         '05_Sign_in__phone___Telegram_': 'login', '06_Profile_setup': 'setup', '07_Home__day_': 'home',
         '10_Request__vehicle___problem': 'request', '11_Confirm_location': 'location', '14_Price_estimate': 'price',
         '17_Searching_for_a_mechanic': 'search', '21_Mechanic_on_the_way': 'enroute', '25_Repair_in_progress': 'repair',
         '22_Quote_to_approve': 'quote', '28_Pay_with_KHQR': 'khqr', '30_Pay_cash': 'cash', '32_Rate_the_mechanic': 'rate',
         '33_Receipt': 'receipt', '34_Cancel__free_': 'cancel', '40_SOS': 'sos', '44_History': 'history', '55_Help': 'help'}
MASK = {'enroute': [(140, 990, 480, 1036)], 'repair': [(120, 1288, 500, 1330)], 'khqr': [(20, 1176, 600, 1280)],
        'cash': [(150, 752, 470, 792)]}
for src, name in NAMES.items():
    im = Image.open(SRC / f'{src}.jpg').convert('RGB')
    d = ImageDraw.Draw(im)
    for box in MASK.get(name, []):
        d.rectangle(box, fill=im.getpixel((box[0] - 6 if box[0] > 10 else 4, box[1] - 4)))
    im.save(OUT / f'{name}.jpg', quality=93)
shutil.copy(r'E:\Phanith.Chhim\AHOLTP0575\FMS\CMS-GATE\help-road-cam\packages\hrc_ui\assets\images\hrc_logo.png', OUT / 'logo.png')
print(len(NAMES), 'screens')
