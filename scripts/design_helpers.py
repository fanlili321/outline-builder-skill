# -*- coding: utf-8 -*-
"""大纲设计图 PIL 渲染助手：封装规范（1920x1080、字号下限、配色、组件、缩略图验收）。

用法：
    import sys; sys.path.insert(0, '/Users/fanlili/.claude/skills/outline-builder/scripts')
    from design_helpers import *
    im, d = canvas()
    title(d, '页面主标题')            # ≥64px，自动记录字号
    ...
    save(im, '459设计_P2_xxx.png')    # 同时输出 *_thumb.png 供小屏验收目检

字号下限（规范第三节）由 font() 记录、save() 汇总告警：
    标题≥64 / 正文要点·结论≥48 / 图表标签≥28 / 来源注·AI标注等边角小字（kind='fine'）豁免。
"""
from PIL import Image, ImageDraw, ImageFont

# ── 规范常量 ──
W, H = 1920, 1080
ORANGE = '#F17640'   # 主色（品牌橙）
CARD = '#FDF0E7'     # 卡片浅橙底
TXT = '#333333'
GRAY = '#8A8A8A'
FONT_TPL = '/Users/fanlili/Library/Fonts/SourceHanSansCN-{}.otf'  # 思源黑体

MIN_SIZE = {'title': 64, 'body': 48, 'label': 28, 'fine': 0}
_used = []  # (size, kind) 记录，save() 时校验


def font(size, weight='Regular', kind='body'):
    """kind: title|body|label|fine。低于该类下限会在 save() 时告警。"""
    _used.append((size, kind))
    return ImageFont.truetype(FONT_TPL.format(weight), size)


def canvas(bg='white'):
    im = Image.new('RGB', (W, H), bg)
    return im, ImageDraw.Draw(im)


def rrect(d, box, r, fill=None, outline=None, width=1):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def title(d, text, size=64, y=88):
    d.text((W // 2, y), text, font=font(size, 'Bold', 'title'), fill='black', anchor='mm')


def band(d, text, y, h=110, size=52, fill=ORANGE, color='white', margin=110):
    """底部橙色结论条：一句核心结论。"""
    rrect(d, (margin, y, W - margin, y + h), 20, fill=fill)
    d.text((W // 2, y + h // 2), text, font=font(size, 'Bold', 'body'), fill=color, anchor='mm')


def stat_card(d, box, label, num, suffix='', label_size=48, num_size=120, suffix_size=48):
    """数据卡：浅橙圆角底 + 标签 + 大号橙色关键数据。无图标（规范：删无信息装饰）。"""
    x0, y0, x1, y1 = box
    rrect(d, box, 28, CARD)
    cx = (x0 + x1) // 2
    ch = y1 - y0
    d.text((cx, y0 + int(ch * 0.30)), label, font=font(label_size, 'Bold', 'body'), fill=TXT, anchor='mm')
    fn = font(num_size, 'Heavy', 'body')
    if suffix:
        fs = font(suffix_size, 'Bold', 'body')
        nw, sw = fn.getlength(num), fs.getlength(' ' + suffix)
        sx = cx - (nw + sw) / 2
        ny = y0 + int(ch * 0.66)
        d.text((sx, ny), num, font=fn, fill=ORANGE, anchor='lm')
        d.text((sx + nw, ny + int(num_size * 0.12)), ' ' + suffix, font=fs, fill=ORANGE, anchor='lm')
    else:
        d.text((cx, y0 + int(ch * 0.66)), num, font=fn, fill=ORANGE, anchor='mm')


def rich(d, x, y, segs, size=48, ls=1.0):
    """行内多色文本；segs=[(text,color,weight)]，'\\n' 换行。返回结束y。正文默认48px。"""
    fx = x
    lh = int(size * 1.55 * ls)
    for text, color, wgt in segs:
        f = font(size, wgt, 'body')
        for i, part in enumerate(text.split('\n')):
            if i > 0:
                y += lh
                fx = x
            d.text((fx, y), part, font=f, fill=color)
            fx += f.getlength(part)
    return y + lh


def flow_arrow(d, cx, y, w=44, h=22, fill=ORANGE):
    """流程箭头（承担先后顺序信息，非装饰）。"""
    d.polygon((cx - w // 2, y, cx + w // 2, y, cx, y + h), fill=fill)


def source_note(d, text, x=110):
    """左下角小字注（口径/待复核说明，规范允许的边角小字）。"""
    d.text((x, H - 54), text, font=font(26, 'Regular', 'fine'), fill=GRAY)


def ai_tag(d):
    """右下角AI示意标注（图内兜底；飞书caption另有统一说明）。"""
    d.text((W - 100, H - 54), '图片来自AI，仅供示意，ppt中会重新作图，并核对数据',
           font=font(24, 'Regular', 'fine'), fill=GRAY, anchor='ra')


def save(im, path, thumb_w=480):
    """保存成品 + 缩略图（宽480px≈手机三分之一屏观感），并校验字号下限。
    渲染后必须 Read 目检缩略图：一眼能看懂主题、关键字可读才算过。"""
    im.save(path)
    tw = thumb_w
    th = int(im.height * tw / im.width)
    im.resize((tw, th), Image.LANCZOS).save(path.replace('.png', '_thumb.png'))
    bad = [(s, k) for s, k in _used if s < MIN_SIZE.get(k, 48)]
    _used.clear()
    if bad:
        print(f'⚠ {path}: 低于字号下限 {sorted(set(bad))} —— 规范要求 标题≥64/正文≥48/图表标签≥28')
    else:
        print(f'✓ {path}（含 _thumb 小屏验收图）')
