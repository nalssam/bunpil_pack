"""PPTX -> PDF(LibreOffice) -> 장표 JPG -> 번호 붙은 모아보기(12장씩). 사용: python render_check.py deck.pptx [출력폴더=pv] [dpi=55]
모아보기로 전체를 보고, 의심 장은 dpi를 올려(-r 100) 한 장씩 확대해서 본다."""
import sys, os, glob, subprocess
from PIL import Image, ImageDraw, ImageFont
src = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else 'pv'; dpi = sys.argv[3] if len(sys.argv) > 3 else '55'
os.makedirs(out, exist_ok=True)
for f in glob.glob(f'{out}/p-*.jpg') + glob.glob(f'{out}/sheet*.jpg'): os.remove(f)
subprocess.run(['soffice', '--headless', '--convert-to', 'pdf', '--outdir', out, src], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
pdf = os.path.join(out, os.path.splitext(os.path.basename(src))[0] + '.pdf')
subprocess.run(['pdftoppm', '-jpeg', '-r', dpi, pdf, f'{out}/p'], check=True)
pages = sorted(glob.glob(f'{out}/p-*.jpg')); tw = 640
try: fnt = ImageFont.truetype(os.path.expanduser('~/.local/share/fonts/Pretendard-Bold.ttf'), 26)
except Exception: fnt = None
for k in range(0, len(pages), 12):
    chunk = pages[k:k + 12]; ims = []
    for j, p in enumerate(chunk):
        im = Image.open(p).convert('RGB'); im = im.resize((tw, int(im.height * tw / im.width)))
        d = ImageDraw.Draw(im); d.rectangle([tw - 64, 0, tw, 36], fill=(19, 44, 61)); d.text((tw - 56, 3), str(k + j + 1), fill='white', font=fnt)
        ims.append(im)
    th = ims[0].height; sheet = Image.new('RGB', (4 * (tw + 8) + 8, 3 * (th + 8) + 8), (120, 120, 120))
    for j, im in enumerate(ims): sheet.paste(im, (8 + (j % 4) * (tw + 8), 8 + (j // 4) * (th + 8)))
    sheet.save(f'{out}/sheet{k // 12 + 1}.jpg', quality=82); print(f'{out}/sheet{k // 12 + 1}.jpg  (장 {k + 1}~{k + len(chunk)})')
print('총', len(pages), '장 · 개별 장:', f'{out}/p-NN.jpg')
