"""Design tokens for the docx report — translated from the render-report
HTML stylesheet, with a print-document hierarchy layered on top (accent
banner section headers, footer page numbers) so the Word document reads as
a designed report rather than default Word output.
"""
from docx.shared import Cm, Pt

# ── palette (HTML hex values, no '#') ──────────────────────────────────
TEXT = "1E293B"          # body   (html: color #1e293b)
TEXT_STRONG = "0F172A"   # titles
TEXT_MUTED = "64748B"    # secondary labels
TEXT_FAINT = "94A3B8"    # captions / footer
TEXT_TABLE = "374151"    # td color
TEXT_TH = "475569"       # th color
BORDER = "E2E8F0"        # card / th border
BORDER_SOFT = "F1F5F9"   # td row divider
FILL_HEADER = "F1F5F9"   # th background
FILL_CARD = "F8FAFC"     # page background reused as card tint
FILL_BANNER = "EFF6FF"   # section-header banner (blue-50)
ACCENT = "3B82F6"        # primary blue
GREEN = "16A34A"
RED = "DC2626"
GRAY = "6B7280"

# default chart series colors, in order, when a series has no explicit color.
# Mappings emit [광고비/전월, 매출/당월] pairs, and the HTML charts color the
# first series slate gray (#94a3b8) and the second light blue (#93c5fd).
CHART_BAR_COLORS = ["94A3B8", "93C5FD", "3B82F6", "A855F7"]
CHART_LINE_COLOR = "EF4444"
# multi-line charts (일일 카테고리별 매출 등): HTML section palette order
CHART_LINE_COLORS = ["3B82F6", "22C55E", "F59E0B", "A855F7", "EF4444",
                     "94A3B8", "EAB308"]
CHART_GRID = "E2E8F0"

# ── typography (print scale: title 22 > section 13 > subhead 11.5 >
#    body 11 > table 9.5/9 > caption 8.5) ──────────────────────────────
# the HTML stylesheet's own font stack ('Noto Sans KR'); Word substitutes a
# system Korean face (typically 맑은 고딕) on machines without it
FONT = "Noto Sans KR"
SIZE_TITLE = Pt(22)
SIZE_PERIOD = Pt(10.5)
SIZE_SECTION = Pt(13)
SIZE_SECTION_NO = Pt(13)   # accent-colored section number in the banner
SIZE_SUBHEAD = Pt(11.5)
SIZE_BODY = Pt(11)
SIZE_TH = Pt(9)
SIZE_TD = Pt(9.5)
SIZE_KPI_LABEL = Pt(9)
SIZE_KPI_VALUE = Pt(16)
SIZE_KPI_DIFF = Pt(10)
SIZE_CAPTION = Pt(8.5)
SIZE_FOOTER = Pt(8.5)

# ── page: A4 landscape throughout — every page shares the wide measure ──
PAGE_W = Cm(29.7)
PAGE_H = Cm(21.0)
MARGIN = Cm(1.6)
CONTENT_W = Cm(29.7 - 2 * 1.6)   # 26.5cm usable width

# analysis text keeps a readable line measure inside the wide page
TEXT_MEASURE_INDENT = Cm(2.0)    # applied to both sides of body paragraphs

# large tables: body rows shown before truncating, after the zero-gross filter
MAX_TABLE_ROWS = 50
# tables larger than this get 매출 0원 rows removed before rendering
ZERO_GROSS_FILTER_MIN_ROWS = 20
# minimum table font when a very wide table must shrink to fit on one line
MIN_TABLE_FONT = 8.0


def diff_color(diff_value):
    """HTML changeColor(): green above zero, red below, gray at zero."""
    if diff_value is None:
        return None
    if diff_value > 0:
        return GREEN
    if diff_value < 0:
        return RED
    return GRAY
