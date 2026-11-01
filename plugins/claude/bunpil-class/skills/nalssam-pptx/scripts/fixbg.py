"""생성 이미지의 배경색을 덱 배경(웜 오프화이트)에 맞추고 가장자리를 부드럽게 녹인다. 사용: python fixbg.py g*.png  -> g*_fx.jpg"""
import sys, numpy as np
from PIL import Image
TARGET = np.array([253, 249, 241], float); SLIDE = np.array([251, 250, 246], float)
for f in sys.argv[1:]:
    a = np.asarray(Image.open(f).convert('RGB')).astype(float); h, w, _ = a.shape; b = max(4, int(min(h, w) * 0.03))
    border = np.concatenate([a[:b].reshape(-1, 3), a[-b:].reshape(-1, 3), a[:, :b].reshape(-1, 3), a[:, -b:].reshape(-1, 3)])
    out = np.clip(a * (TARGET / np.median(border, 0)), 0, 255)          # 가장자리 중앙값 = 목표 크림색
    yy = np.linspace(0, 1, h)[:, None]; xx = np.linspace(0, 1, w)[None, :]
    d = np.minimum(np.minimum(yy, 1 - yy) * h, np.minimum(xx, 1 - xx) * w) / (0.06 * min(h, w))
    m = np.clip(d, 0, 1)[..., None]; m = m * m * (3 - 2 * m)
    out = out * m + SLIDE * (1 - m)                                      # 테두리를 슬라이드색으로 페더링
    o = f.rsplit('.', 1)[0] + '_fx.jpg'; Image.fromarray(out.astype('uint8')).save(o, quality=92); print(f, '->', o)
