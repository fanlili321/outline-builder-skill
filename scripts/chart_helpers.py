# -*- coding: utf-8 -*-
"""直播大纲配图通用工具（458期跑通版提炼）。
用法：sys.path.insert(0, '本目录') 后 import chart_helpers as C
完整实例（星级分色叠加/双轴/月度表）见 Desktop/范丽丽./live-ppt-tool/outline_458/render_458.py
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator
from datetime import datetime

plt.rcParams['font.family'] = 'Source Han Sans CN'   # 思源黑体，全套物料统一字体
plt.rcParams['axes.unicode_minus'] = False

# ── 品牌配色（与PPT设计素材库一致，勿自造颜色） ──
ORANGE = '#F17640'   # 主色，第1条线/主角指数
LBLUE = '#7CA7E0'    # 第2条线
GRAY = '#929292'     # 第3条线/大盘基准
GOLD = '#E5A200'     # 星级线（右轴），金黄加深保证白底可读
RED = '#E54C5E'      # 1星段/警示
YELLOW = '#FFBF00'   # 3星段
GREEN = '#75BD42'    # 4星段
DGREEN = '#1E9E7B'   # ≥5星段
TXT = '#333333'
SRC_GRAY = '#999999'
LINE_COLORS = [ORANGE, LBLUE, GRAY, '#4874CB', RED, '#D53A78', YELLOW]  # 多线按序取
# ── 字号档位（471期定稿，投直播大屏用；改字号只改这里，别在各处写死） ──
TITLE_SIZE = 32     # 图表主标题（原26）
TICK_SIZE = 20      # 横纵坐标刻度、轴标签（原15）
LEGEND_SIZE = 20    # 图例，与刻度同档（原15）
TICK_SIZE_2ND = 18  # 副轴刻度/轴标签，比主轴小一档以区分主次（原14）
TABLE_SIZE = 18     # 图下方数据表（原14.5）
SRC_SIZE = 16       # 底部来源注/口径注，最小一档但要能看清（原12）
SRC = '数据来源：Wind'                            # 默认来源（指数/行情类图表），绝大多数走势图/数据图用这个
SRC_STAR = '数据来源：Wind、银行螺丝钉'              # 指数/行情类图表若带星级/估值表，才加"银行螺丝钉"
SRC_PORTFOLIO_BASE = '东方证券、雪球基金'            # 投顾组合净值类图表的固定基础来源，不用Wind打底
STD_CAPTION = '图片来自AI，仅供示意，ppt中会重新作图，并核对数据'


def common_pct(cache, codes_names, s, e):
    """按共同交易日对齐并归一化为相对首日涨跌幅（多线绝不断线的关键）。
    cache: {code: {'data': [{'date','close'}]}}；codes_names: [(code, 显示名)]
    返回 (days, [(name, vals)])，vals为小数(0.05=5%)"""
    raw = {c: {x['date']: x['close'] for x in cache[c]['data'] if s <= x['date'] <= e}
           for c, _ in codes_names}
    days = sorted(set.intersection(*[set(v.keys()) for v in raw.values()]))
    if not days:
        raise RuntimeError(f'无共同交易日: {s}~{e}')
    out = []
    for c, name in codes_names:
        base = raw[c][days[0]]
        out.append((name, [raw[c][d] / base - 1 for d in days]))
    return days, out


def style_ax(ax):
    """统一底纹：去上右边框、浅灰横网格"""
    for sp in ('top', 'right'):
        ax.spines[sp].set_visible(False)
    for sp in ('left', 'bottom'):
        ax.spines[sp].set_color('#CCCCCC')
    ax.grid(axis='y', color='#E8E8E8', linewidth=0.8)
    ax.set_axisbelow(True)


def pct_axis(ax, all_vals):
    """左轴百分比整数刻度，范围含极值"""
    lo, hi = min(all_vals), max(all_vals)
    ax.yaxis.set_major_locator(MaxNLocator(nbins=8))
    ticks = ax.get_yticks()
    ax.set_ylim(min(lo * 1.08, ticks[0]), max(hi * 1.08, ticks[-1]))
    ax.yaxis.set_major_formatter(lambda v, p: f'{v*100:.0f}%')
    ax.tick_params(colors=TXT, labelsize=TICK_SIZE)


def fmt_xaxis(ax, dts, every_n_years=None):
    """X轴 YYYY.M 格式；长周期(>4年)传 every_n_years=2 更均匀"""
    if every_n_years:
        ax.xaxis.set_major_locator(mdates.YearLocator(every_n_years))
    else:
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=4, maxticks=7))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y.%-m'))
    ax.tick_params(colors=TXT, labelsize=TICK_SIZE)


def base_chart(title, days, data, figsize=(13.5, 7), colors=None):
    """标准多线走势图：标题+图例靠左置顶+样式齐活，返回 (fig, ax, dts)"""
    dts = [datetime.strptime(d, '%Y-%m-%d') for d in days]
    fig, ax = plt.subplots(figsize=figsize)
    for (name, vals), c in zip(data, colors or LINE_COLORS):
        ax.plot(dts, vals, color=c, linewidth=2.4, label=name)
    style_ax(ax)
    pct_axis(ax, [v for _, vals in data for v in vals])
    fmt_xaxis(ax, dts)
    ax.set_title(title, fontsize=TITLE_SIZE, fontweight='bold', color='black', pad=44)
    ax.legend(loc='lower left', bbox_to_anchor=(0.0, 1.0), ncol=min(len(data), 4),
              frameon=False, fontsize=LEGEND_SIZE, handlelength=1.6, columnspacing=1.2)
    return fig, ax, dts


def add_right_axis(ax, dts, vals, label='红利星级', color=GOLD, ylim=(0.5, 5.5), ticks=(1, 2, 3, 4, 5)):
    """副轴叠加线（星级等1-5类指标），虚线区分主线"""
    ax2 = ax.twinx()
    ax2.plot(dts, vals, color=color, linewidth=2.2, linestyle=(0, (5, 2)), zorder=2)
    ax2.set_ylim(*ylim)
    ax2.set_yticks(list(ticks))
    ax2.set_ylabel(label, fontsize=TICK_SIZE_2ND, color=color)
    ax2.tick_params(colors=color, labelsize=TICK_SIZE_2ND)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_color('#CCCCCC')
    return ax2


def add_source(fig, end_date, note=None, star=False, portfolio=False, wind=False):
    """右下来源（必加），note=左下口径说明（可选）。两套互斥口径，按图表内容选一套：
    - 指数/行情类图表（默认）：只写"Wind"；star=True 才追加"、银行螺丝钉"（星级/估值表相关内容）。
    - 投顾组合净值类图表：portfolio=True，固定来源是"东方证券、雪球基金"；
      wind=True 在前面加"Wind、"（图里还用了Wind取的数据）；star=True 在后面加"、银行螺丝钉"（图里带了螺丝钉星级）。
    """
    if portfolio:
        parts = []
        if wind:
            parts.append('Wind')
        parts.append(SRC_PORTFOLIO_BASE)
        if star:
            parts.append('银行螺丝钉')
        src = '数据来源：' + '、'.join(parts)
    else:
        src = SRC_STAR if star else SRC
    fig.text(0.985, 0.015, f'{src}，截至{end_date}', ha='right', fontsize=SRC_SIZE, color=SRC_GRAY)
    if note:
        fig.text(0.13, 0.015, note, ha='left', fontsize=SRC_SIZE, color=TXT)


def monthly_returns(cache, code, s, e):
    """月度涨跌幅：月末收盘/上月末收盘-1，首月以区间首日为基准。
    返回 [(YYYY-MM, 涨跌幅小数)]，末月天然是"至今"口径"""
    d = {x['date']: x['close'] for x in cache[code]['data'] if s <= x['date'] <= e}
    ds = sorted(d.keys())
    m_last = {}
    for day in ds:
        m_last[day[:7]] = d[day]
    prev = d[ds[0]]
    out = []
    for m in sorted(m_last):
        out.append((m, m_last[m] / prev - 1))
        prev = m_last[m]
    return out


def add_table(fig, headers, rows, rect=(0.08, 0.10, 0.87, 0.22), first_col_w=0.22):
    """图下方数据表：橙表头白字、偶数行浅灰（PPT表格样式）。
    rect=(left,bottom,width,height)；行多时调大height并加大figsize"""
    tab_ax = fig.add_axes(rect)
    tab_ax.axis('off')
    tbl = tab_ax.table(cellText=rows, colLabels=headers, loc='center', cellLoc='center')
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(TABLE_SIZE)
    tbl.scale(1, 2.1)
    for j in range(len(headers)):
        cell = tbl[0, j]
        cell.set_facecolor(ORANGE)
        cell.set_edgecolor('#FFFFFF')
        cell.get_text().set_color('white')
        cell.get_text().set_fontweight('bold')
    for i in range(1, len(rows) + 1):
        for j in range(len(headers)):
            cell = tbl[i, j]
            cell.set_facecolor('#FFFFFF' if i % 2 else '#F5F5F5')
            cell.set_edgecolor('#DDDDDD')
    for i in range(len(rows) + 1):
        tbl[i, 0].set_width(first_col_w)
    return tbl


def save(fig, path):
    fig.savefig(path, dpi=150, facecolor='white', bbox_inches='tight', pad_inches=0.25)
    plt.close(fig)
    print('saved', path)
