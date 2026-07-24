"""Design tokens translated from the HTML report's stylesheet.

Every color/size mirrors a value in the render-report HTML scaffold or
section markup so the deck reads as the same design system. Slide geometry
is 16:9 (13.333in x 7.5in).
"""
from pptx.util import Emu, Pt

# ── palette (HTML hex values, no '#') ──────────────────────────────────
TEXT = "1E293B"          # body   (html: color #1e293b)
TEXT_STRONG = "0F172A"   # titles
TEXT_MUTED = "64748B"    # secondary labels
TEXT_FAINT = "94A3B8"    # footer / captions
TEXT_TABLE = "374151"    # td color
TEXT_TH = "475569"       # th color
BORDER = "E2E8F0"        # card / th border
BORDER_SOFT = "F1F5F9"   # td row divider
FILL_PAGE = "F8FAFC"     # html body background
FILL_CARD = "FFFFFF"     # card background
FILL_HEADER = "F1F5F9"   # th background
ACCENT = "3B82F6"        # primary blue
GREEN = "16A34A"
RED = "DC2626"
GRAY = "6B7280"

# default chart series colors, in order, when a series has no explicit color.
# Mappings emit [광고비/전월, 매출/당월] pairs, and the HTML charts color the
# first series slate gray (#94a3b8) and the second light blue (#93c5fd).
CHART_BAR_COLORS = ["94A3B8", "93C5FD", "3B82F6", "A855F7"]
CHART_LINE_COLOR = "EF4444"
CHART_GRID = "E2E8F0"

# ── typography ─────────────────────────────────────────────────────────
FONT = "Malgun Gothic"   # 맑은 고딕 — Windows-native, closest to Noto Sans KR

# Typography scale — one deliberate step between levels so the hierarchy
# reads at a glance: cover 32 > slide title 18 > subhead 13 > body 12 >
# table 10/9.5 > captions 9.
SIZE_COVER_TITLE = Pt(32)
SIZE_COVER_PERIOD = Pt(14)
SIZE_SLIDE_TITLE = Pt(18)
SIZE_DIVIDER = Pt(24)
SIZE_FOOTER = Pt(9)
SIZE_TH = Pt(9.5)
SIZE_TD = Pt(10)
SIZE_BODY = Pt(12)
SIZE_BODY_SUBHEAD = Pt(13)
SIZE_KPI_LABEL = Pt(11)
SIZE_KPI_VALUE = Pt(26)
SIZE_KPI_DIFF = Pt(12)
SIZE_TABLE_NOTE = Pt(9.5)

# ── slide geometry (EMU) ───────────────────────────────────────────────
SLIDE_W = Emu(12192000)  # 13.333 in
SLIDE_H = Emu(6858000)   # 7.5 in
MARGIN = Emu(548640)     # 0.6 in

TITLE_TOP = Emu(365760)      # 0.4 in
TITLE_H = Emu(457200)        # 0.5 in
CONTENT_TOP = Emu(1005840)   # 1.1 in — below the title band
CONTENT_W = Emu(12192000 - 2 * 548640)
CONTENT_H = Emu(6858000 - 1005840 - 548640)  # bottom margin above footer
FOOTER_TOP = Emu(6858000 - 402336)           # 0.44 in tall footer strip

# body rows shown per table slide before truncating to "상위 N개"
MAX_TABLE_ROWS = 12


def diff_color(diff_value):
    """HTML changeColor(): green above zero, red below, gray at zero."""
    if diff_value is None:
        return None
    if diff_value > 0:
        return GREEN
    if diff_value < 0:
        return RED
    return GRAY
