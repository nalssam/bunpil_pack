"""덱에 Pretendard '전체' 글꼴을 심는다(EOT, 비압축). 이미 들어 있는 부분(subset) 임베드는 전체 글꼴로 교체한다.
부분 임베드는 새로 쓴 글자가 얇은 대체 글꼴로 보이게 만든다(모바일 PowerPoint에서 특히). 저장의 '마지막' 단계에 실행.
사용: python embed_fonts.py in.pptx out.pptx [글꼴폴더=~/.local/share/fonts]"""
import sys, re, os, struct, zipfile
from lxml import etree
from fontTools.ttLib import TTFont

SRC, DST = sys.argv[1], sys.argv[2]
FONTDIR = sys.argv[3] if len(sys.argv) > 3 else os.path.expanduser('~/.local/share/fonts')
MAP = {  # typeface -> {칸: ttf}   (덱 글꼴 이름과 같아야 한다)
    'Pretendard': {'regular': 'Pretendard-Regular.ttf', 'bold': 'Pretendard-Bold.ttf'},
    'Pretendard ExtraBold': {'regular': 'Pretendard-ExtraBold.ttf'},
    'Pretendard Medium': {'regular': 'Pretendard-Medium.ttf'},
}
NS = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
RELNS = 'http://schemas.openxmlformats.org/package/2006/relationships'
FONT_REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/font'
P, R = '{%s}' % NS['p'], '{%s}' % NS['r']


def u16(s):
    b = s.encode('utf-16le'); return struct.pack('<H', len(b)) + b


def make_eot(ttf, family, style):
    data = open(ttf, 'rb').read(); f = TTFont(ttf); os2 = f['OS/2']; pn = os2.panose
    pan = bytes([pn.bFamilyType, pn.bSerifStyle, pn.bWeight, pn.bProportion, pn.bContrast,
                 pn.bStrokeVariation, pn.bArmStyle, pn.bLetterForm, pn.bMidline, pn.bXHeight])
    ver = f['name'].getDebugName(5) or 'Version 1.0'
    body = pan + struct.pack('<BBIHH', 0x81, 1 if os2.fsSelection & 1 else 0, os2.usWeightClass, os2.fsType, 0x504C)
    body += struct.pack('<IIII', os2.ulUnicodeRange1, os2.ulUnicodeRange2, os2.ulUnicodeRange3, os2.ulUnicodeRange4)
    body += struct.pack('<II', os2.ulCodePageRange1, os2.ulCodePageRange2)
    body += struct.pack('<I', f['head'].checkSumAdjustment) + b'\0' * 16
    body += b'\0\0' + u16(family + '\0') + b'\0\0' + u16(style + '\0') + b'\0\0' + u16(ver) + b'\0\0' + u16(family)
    body += b'\0\0' + struct.pack('<H', 0) + struct.pack('<II', 0, 0)
    body += b'\0\0' + struct.pack('<H', 0) + struct.pack('<II', 0, 0)
    return struct.pack('<IIII', 16 + len(body) + len(data), len(data), 0x00020002, 0) + body + data


def panose_hex(ttf):
    pn = TTFont(ttf)['OS/2'].panose
    return ''.join('%02X' % v for v in (pn.bFamilyType, pn.bSerifStyle, pn.bWeight, pn.bProportion, pn.bContrast,
                                        pn.bStrokeVariation, pn.bArmStyle, pn.bLetterForm, pn.bMidline, pn.bXHeight))


zin = zipfile.ZipFile(SRC)
files = {i.filename: zin.read(i.filename) for i in zin.infolist()}
order = [i.filename for i in zin.infolist()]
pres = etree.fromstring(files['ppt/presentation.xml'])
rels = etree.fromstring(files['ppt/_rels/presentation.xml.rels'])
ct = files['[Content_Types].xml'].decode('utf8')
if 'Extension="fntdata"' not in ct:
    ct = ct.replace('<Default ', '<Default Extension="fntdata" ContentType="application/x-fontdata"/><Default ', 1)
    files['[Content_Types].xml'] = ct.encode('utf8')
rid_n = max([int(m) for r in rels for m in re.findall(r'^rId(\d+)$', r.get('Id'))] + [0])
font_n = max([int(m) for n in files for m in re.findall(r'^ppt/fonts/font(\d+)\.fntdata$', n)] + [0])
lst = pres.find('p:embeddedFontLst', NS)
if lst is None:
    lst = etree.Element(P + 'embeddedFontLst')
    anchor = pres.find('p:notesSz', NS)
    if anchor is None: anchor = pres.find('p:sldSz', NS)
    anchor.addnext(lst)


def part_of(rid):
    for r in rels:
        if r.get('Id') == rid: return 'ppt/' + r.get('Target')
    raise KeyError(rid)


done = []
for face, slots in MAP.items():
    ef = next((e for e in lst.findall('p:embeddedFont', NS) if e.find('p:font', NS).get('typeface') == face), None)
    first_ttf = os.path.join(FONTDIR, next(iter(slots.values())))
    if not os.path.exists(first_ttf): sys.exit(f'글꼴 없음: {first_ttf}')
    if ef is None:
        ef = etree.SubElement(lst, P + 'embeddedFont')
        etree.SubElement(ef, P + 'font', typeface=face, panose=panose_hex(first_ttf), pitchFamily='50', charset='-127')
    for slot, fn in slots.items():
        eot = make_eot(os.path.join(FONTDIR, fn), face, 'Bold' if slot == 'bold' else 'Regular')
        el = ef.find('p:' + slot, NS)
        if el is not None:                                   # 기존 칸: 부품 내용만 교체
            target = part_of(el.get(R + 'id'))
        else:                                                # 새 칸: 관계·부품·요소 추가
            rid_n += 1; font_n += 1; target = f'ppt/fonts/font{font_n}.fntdata'
            etree.SubElement(rels, '{%s}Relationship' % RELNS, Id=f'rId{rid_n}', Type=FONT_REL, Target=f'fonts/font{font_n}.fntdata')
            el = etree.Element(P + slot); el.set(R + 'id', f'rId{rid_n}')
            prev = [c for c in ef if c.tag in (P + 'font', P + 'regular', P + 'bold')]
            prev[-1].addnext(el)
            order.append(target)
        files[target] = eot; done.append((face, slot, len(eot)))
pres.set('embedTrueTypeFonts', '1'); pres.attrib.pop('saveSubsetFonts', None)   # 다시 저장해도 '모든 문자' 임베드 유지
files['ppt/presentation.xml'] = etree.tostring(pres, xml_declaration=True, encoding='UTF-8', standalone=True)
files['ppt/_rels/presentation.xml.rels'] = etree.tostring(rels, xml_declaration=True, encoding='UTF-8', standalone=True)
with zipfile.ZipFile(DST, 'w', zipfile.ZIP_DEFLATED) as zo:
    for n in order: zo.writestr(n, files[n])
from pptx import Presentation; Presentation(DST)           # 다시 열어 보는 검증
for d in done: print('임베드', *d)
print('저장', DST)
