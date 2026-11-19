# Renderer for the 19 November 2026 front page.
# Pure Python standard library: draws a 1024x1024 newspaper front page
# and writes it as a PNG (zlib). No network, no randomness, no timestamps.

import os
import struct
import zlib

W, H = 1024, 1024

# ---- palette ----
INK = (18, 18, 18)
PAPER = (250, 247, 238)
NAVY = (20, 33, 61)
NAVY2 = (28, 46, 84)
RED = (178, 34, 34)
GOLD = (198, 148, 52)
TEAL = (14, 110, 110)
GREY = (110, 110, 104)
LIGHT = (232, 228, 216)
LINE = (180, 175, 160)
BLUE = (36, 84, 160)
GREEN = (34, 120, 70)
ORANGE = (214, 110, 30)

# ---- 5x7 bitmap font (uppercase, digits, punctuation) ----
def _g(*rows):
    return rows

FONT = {
    'A': _g("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': _g("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': _g("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': _g("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': _g("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': _g("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': _g("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': _g("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': _g("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': _g("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': _g("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': _g("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': _g("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': _g("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': _g("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': _g("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': _g("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': _g("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': _g("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': _g("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': _g("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': _g("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': _g("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': _g("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': _g("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': _g("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': _g("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': _g("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': _g("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': _g("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    '4': _g("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': _g("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': _g("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': _g("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': _g("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': _g("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    '.': _g("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': _g("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ':': _g("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': _g("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    '!': _g("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': _g("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    '-': _g("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "'": _g("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': _g("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    '(': _g("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': _g("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '/': _g("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '%': _g("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '$': _g("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '&': _g("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '+': _g("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '=': _g("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '*': _g("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    '#': _g("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    '@': _g("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    '_': _g("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    ' ': _g("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '·': _g("00000", "00000", "00000", "01100", "01100", "00000", "00000"),
    '—': _g("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    'X2': _g("10001", "01010", "00100", "01010", "10001", "10001", "10001"),
}

CHAR_W = 6  # 5 px glyph + 1 px gap


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg[0] for _ in range(w * h * 3))
        # fill properly
        for i in range(w * h):
            self.px[i * 3] = bg[0]
            self.px[i * 3 + 1] = bg[1]
            self.px[i * 3 + 2] = bg[2]

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = c[0]
            self.px[i + 1] = c[1]
            self.px[i + 2] = c[2]

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, c)

    def hline(self, x, y, w, c, th=1):
        self.rect(x, y, w, th, c)

    def vline(self, x, y, h, c, th=1):
        self.rect(x, y, th, h, c)

    def line(self, x0, y0, x1, y1, c):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c, fill=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill:
                    if d <= r * r:
                        self.set(xx, yy, c)
                else:
                    if r * r - 2 * r <= d <= r * r:
                        self.set(xx, yy, c)

    def poly(self, pts, c):
        # scanline fill
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    t = (y - y0) / (y1 - y0)
                    xs.append(x0 + t * (x1 - x0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                for x in range(int(xs[k]), int(xs[k + 1]) + 1):
                    self.set(x, y, c)

    def text(self, x, y, s, c, scale=1):
        s = s.upper()
        cx = x
        for ch in s:
            g = FONT.get(ch)
            if g is None:
                ch = ' '
                g = FONT[' ']
            for r in range(7):
                row = g[r]
                for col in range(5):
                    if row[col] == '1':
                        self.rect(cx + col * scale, y + r * scale, scale, scale, c)
            cx += CHAR_W * scale
        return cx

    def text_w(self, s, scale=1):
        return len(s.upper()) * CHAR_W * scale

    def text_center(self, cx, y, s, c, scale=1):
        w = self.text_w(s, scale)
        self.text(cx - w // 2, y, s, c, scale)

    def wrap(self, s, max_w, scale=1):
        words = s.split(' ')
        lines = []
        cur = ''
        for w in words:
            trial = (cur + ' ' + w).strip()
            if self.text_w(trial, scale) <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines


def png_bytes(cv):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)
        raw.extend(cv.px[y * cv.w * 3:(y + 1) * cv.w * 3])
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        out = struct.pack('>I', len(data)) + tag + data
        out += struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
        return out

    ihdr = struct.pack('>IIBBBBB', cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr)
            + chunk(b'IDAT', comp) + chunk(b'IEND', b''))


# ---- illustrations (flat vector style) ----

def ill_summit(cv, x, y, w, h):
    # sky
    cv.rect(x, y, w, h, (214, 228, 240))
    # skyline
    cv.rect(x + 8, y + h - 46, 30, 46, NAVY2)
    cv.rect(x + 42, y + h - 60, 24, 60, (70, 90, 130))
    cv.rect(x + 70, y + h - 38, 34, 38, NAVY2)
    cv.rect(x + w - 110, y + h - 52, 26, 52, (70, 90, 130))
    cv.rect(x + w - 80, y + h - 66, 30, 66, NAVY2)
    cv.rect(x + w - 44, y + h - 40, 34, 40, (70, 90, 130))
    # sun
    cv.circle(x + w // 2, y + 22, 12, GOLD)
    # three flag poles + flags
    pole_y = y + 18
    pole_h = h - 52
    flags = [
        ((178, 34, 34), (255, 255, 255)),   # red flag
        ((36, 84, 160), (255, 255, 255)),   # blue flag
        ((34, 120, 70), (255, 215, 0)),      # green/gold flag
    ]
    xs = [x + w // 2 - 78, x + w // 2 - 6, x + w // 2 + 66]
    for (fx, (fc, sc)) in zip(xs, flags):
        cv.vline(fx, pole_y, pole_h, INK, 2)
        cv.rect(fx + 2, pole_y, 34, 20, fc)
        cv.circle(fx + 12, pole_y + 10, 3, sc)
    # table
    cv.rect(x + 10, y + h - 14, w - 20, 10, (120, 72, 40))
    cv.rect(x + 10, y + h - 18, w - 20, 4, (150, 100, 55))


def ill_ipo(cv, x, y, w, h):
    cv.rect(x, y, w, h, (224, 240, 224))
    # bars
    base = y + h - 22
    bars = [(16, 26), (52, 40), (88, 34), (124, 56), (160, 48), (196, 74), (232, 92)]
    for bx, bh in bars:
        cv.rect(x + bx, base - bh, 26, bh, TEAL)
    cv.rect(x + 232, base - 92, 26, 92, GOLD)
    # arrow
    cv.line(x + 12, base - 30, x + w - 30, y + 14, RED)
    cv.line(x + w - 30, y + 14, x + w - 52, y + 14, RED)
    cv.line(x + w - 30, y + 14, x + w - 30, y + 36, RED)
    # bell
    bx = x + w - 62
    by = y + h - 52
    cv.poly([(bx, by), (bx + 26, by), (bx + 32, by + 22), (bx - 6, by + 22)], GOLD)
    cv.circle(bx + 13, by + 26, 4, GOLD)
    # ticker tape
    cv.rect(x, y + h - 14, w, 14, INK)
    cv.text(x + 6, y + h - 12, "ANT $111.50 +34%", PAPER, 1)


def ill_icj(cv, x, y, w, h):
    cv.rect(x, y, w, h, (232, 226, 214))
    # courthouse
    cx = x + w // 2
    cv.rect(cx - 96, y + h - 30, 192, 8, NAVY2)
    for i in range(5):
        px = cx - 84 + i * 38
        cv.rect(px, y + 44, 14, h - 74, NAVY2)
    cv.rect(cx - 100, y + 34, 200, 10, NAVY2)
    cv.poly([(cx - 112, y + 34), (cx + 112, y + 34), (cx, y + 8)], RED)
    cv.circle(cx, y + 20, 5, GOLD)
    # scales
    sx = x + w - 58
    sy = y + h - 58
    cv.vline(sx, sy - 26, 26, INK, 2)
    cv.line(sx - 18, sy - 26, sx + 18, sy - 26, INK)
    cv.line(sx - 18, sy - 26, sx - 24, sy - 10, INK)
    cv.line(sx - 18, sy - 26, sx - 12, sy - 10, INK)
    cv.line(sx + 18, sy - 26, sx + 12, sy - 10, INK)
    cv.line(sx + 18, sy - 26, sx + 24, sy - 10, INK)
    cv.poly([(sx - 26, sy - 10), (sx - 10, sy - 10), (sx - 18, sy - 2)], GOLD)
    cv.poly([(sx + 10, sy - 10), (sx + 26, sy - 10), (sx + 18, sy - 2)], GOLD)


# ---- content (all verified for 19 Nov 2026) ----

LEADS = [
    ("ASIA-PACIFIC  ·  DIPLOMACY", "TRUMP, XI AND PUTIN MEET IN SHENZHEN",
     "First-ever three-way summit at APEC ends with a 'peace declaration' after 90 minutes. Ukraine and Iran go unmentioned.", ill_summit),
    ("TECHNOLOGY  ·  MARKETS", "ANTHROPIC'S $81.3BN IPO SMASHES RECORD",
     "Claude maker prices at $83 a share, tops SpaceX's record, then opens 34% higher on Nasdaq as ANT.", ill_ipo),
    ("LAW  ·  HUMAN RIGHTS", "MYANMAR COMMITTED GENOCIDE, TOP UN COURT RULES",
     "ICJ finds genocidal intent against the Rohingya; about 10,000 killed. A first for the world court.", ill_icj),
]

SECONDARY = [
    ("GAZA", "ISRAEL ENDS GAZA GROUND OPERATION",
     "Tanks pull back after a rare push past the Yellow Line near Nuseirat and Bureij."),
    ("UKRAINE", "THIRD STRIKE ON CRIMEA BRIDGE HALTS RAIL",
     "Kyiv hits the Kerch span again as Zelenskyy meets US envoys in Berlin."),
    ("SAUDI ARABIA", "HOUTHI MISSILE DAMAGES RIYADH TOWER",
     "Blast hits the PIF Tower, the kingdom's tallest, as new attacks are reported."),
    ("IRAN", "US STRIKE ON QESHM; IRAN HITS BACK",
     "Tehran says it struck a US base in Kuwait; carriers leave the Gulf. (Reported)"),
    ("ARCTIC", "DENMARK BACKS GREENLAND DEAL 109-0",
     "Parliament ratifies the US security pact, easing Trump's Arctic standoff."),
    ("BANGLADESH", "FOUR KILLED AS UNREST SPREADS",
     "Yunus ancestral home set ablaze amid an opposition shutdown."),
    ("CLIMATE", "COP31 TALKS ENTER FINAL STRETCH",
     "Fossil-fuel phase-out wording still unresolved as the deadline nears."),
    ("MARKETS", "FED MINUTES HIT STOCKS; BITCOIN SLIPS",
     "S&P 500 falls a fifth straight day; gold nears a 14-month low."),
    ("SPORT", "JAZZ END LAKERS' NINE-GAME RUN",
     "Utah wins 109-97; Denver rallies past Boston 105-101."),
]

NUMBERS = [
    ("$81.3BN", "ANTHROPIC IPO, THE LARGEST EVER"),
    ("109-0", "DENMARK'S GREENLAND VOTE"),
    ("10,000", "ROHINGYA KILLED, PER THE ICJ"),
    ("1,650", "KILLED IN GAZA SINCE THE CEASEFIRE"),
]

TIMELINE = [
    ("02:10", "DENVER RALLIES PAST BOSTON 105-101"),
    ("09:15", "ANTHROPIC IPO PRICED AT $83, A RECORD $81.3BN"),
    ("11:00", "DENMARK BACKS GREENLAND DEAL 109-0"),
    ("12:31", "ISRAEL SAYS CENTRAL GAZA OPERATION IS OVER"),
    ("15:41", "EU URGES ALL SIDES TO HONOUR GAZA CEASEFIRE"),
    ("18:44", "EUROPE AND US PRESENT UNITED FRONT ON UKRAINE"),
]

BRIEFS = [
    "S. KOREA COURT ORDERS RETRIAL OF EX-PM HAN",
    "JAPAN TOBACCO TAKES $8.9BN RUSSIA CHARGE",
    "RAKUTEN SECURITIES RACES TO CONTAIN BREACH",
    "JAPAN PM TAKAICHI TALKS WITH PUTIN",
    "TRUMP AND MARCOS HAIL ALLIANCE, TRADE TIES",
    "SPAIN SNAP VOTE RAISES FAR-RIGHT FEARS",
    "IAEA: N. KOREA EXPANDING ENRICHMENT",
    "S. KOREA'S LEE URGES DIALOGUE WITH NORTH",
    "RIO TINTO PAYS $250M OVER PNG MINE LEGACY",
    "TRUMP ASKS COURT TO BLOCK MIGRANT PROTECTIONS",
    "BEGICH KEEPS ALASKA'S SOLE HOUSE SEAT",
    "JEFFRIES NOMINATED FOR HOUSE SPEAKER",
    "LPG TANKER GAS HUSKY SINKS OFF BULGARIA",
    "NEARLY 1 IN 4 CHILDREN LIVE IN CONFLICT ZONES",
    "TASMANIA ASSISTED DEATHS UP 129% IN 2 YEARS",
    "TRUMP: US WILL 'SEE WHAT HAPPENS' ON IRAN",
    "CARNEY WRAPS APEC WITH CHINA TRADE GAINS",
    "FIFA: DIALLO, TASHIMA TO CHALLENGE INFANTINO",
    "S. AFRICA BEAT BANGLADESH BY 9 WICKETS",
    "ENGLAND BEAT AUSTRALIA BY 97 RUNS IN ODI",
    "PHOENIX THRASH SACRAMENTO 128-107 IN NBA",
    "DETROIT BEAT NEW ORLEANS 122-109 IN NBA",
    "NO. 12 ARIZONA UPSETS NO. 3 UCONN 85-79",
    "NHL: UTAH ENDS SKID; BOSTON BEAT DETROIT 4-1",
    "PERSIB BANDUNG HIT SHAN UNITED 6-0",
    "SVAY RIENG BEAT PORT 4-1; JOHOR DT WIN 3-1",
    "QUANTUM COMPUTERS MAY BREAK BANK CODES: IOSCO",
    "WALMART SHARES SLIP AFTER Q3 RESULTS",
    "PALO ALTO NETWORKS CLIMBS ON EARNINGS",
    "NVIDIA FALLS 2.9% DESPITE BEATING FORECASTS",
    "GAZA PEACE PLAN SCORES 4 OF 26 IN REVIEW",
    "NEPAL WINS AWARD; NORWAY NAMED FOSSIL OF DAY",
    "RIGHTS GROUP HAILS RELEASE OF 236 PROTESTERS",
    "GTA 6 RELEASE DAY SPARKS MEMECOIN FRENZY",
]

N_STORIES = len(LEADS) + len(SECONDARY) + len(BRIEFS)


def build(out_path):
    cv = Canvas(W, H, PAPER)
    M = 16
    # ---- masthead ----
    cv.rect(0, 0, W, 96, NAVY)
    cv.rect(0, 96, W, 3, GOLD)
    cv.text_center(W // 2, 10, "THE WORLD TODAY", (200, 200, 190), 1)
    cv.text_center(W // 2, 26, "THURSDAY 19 NOVEMBER 2026", PAPER, 3)
    cv.text_center(W // 2, 62, "%d STORIES  ·  7 REGIONS  ·  ONE PAGE" % N_STORIES, GOLD, 2)
    cv.text_center(W // 2, 82, "EVERY STORY ON THIS PAGE HAPPENED, OR WAS FIRST REPORTED, ON THIS DAY.",
                   (200, 200, 190), 1)
    y = 108
    # ---- leads ----
    col_w = (W - 2 * M - 2 * 12) // 3
    for i, (tag, head, body, ill) in enumerate(LEADS):
        x = M + i * (col_w + 12)
        cv.text(x, y, tag, RED, 1)
        ill(cv, x, y + 12, col_w, 108)
        hy = y + 128
        lines = cv.wrap(head, col_w, 2)
        for ln in lines[:3]:
            cv.text(x, hy, ln, INK, 2)
            hy += 17
        for ln in cv.wrap(body, col_w, 1)[:3]:
            cv.text(x, hy, ln, (60, 60, 55), 1)
            hy += 10
        cv.vline(x + col_w + 6, y, 232, LINE)
    y = 108 + 240
    cv.hline(M, y, W - 2 * M, INK, 2)
    y += 10
    # ---- secondary: 3 cols x 3 rows ----
    cell_w = col_w
    cell_h = 74
    for i, (tag, head, body) in enumerate(SECONDARY):
        r, c = divmod(i, 3)
        x = M + c * (cell_w + 12)
        cy = y + r * cell_h
        cv.rect(x, cy, 34, 34, NAVY2)
        cv.text_center(x + 17, cy + 13, tag[0], GOLD, 2)
        tx = x + 42
        cv.text(tx, cy, tag, RED, 1)
        hl = cv.wrap(head, cell_w - 42, 1)
        hy = cy + 11
        for ln in hl[:2]:
            cv.text(tx, hy, ln, INK, 1)
            hy += 10
        for ln in cv.wrap(body, cell_w - 42, 1)[:2]:
            cv.text(tx, hy, ln, (60, 60, 55), 1)
            hy += 10
    y += 3 * cell_h + 6
    cv.hline(M, y, W - 2 * M, INK, 2)
    y += 8
    # ---- by the numbers ----
    cv.text(M, y, "BY THE NUMBERS", RED, 2)
    y += 22
    nbox = (W - 2 * M - 3 * 10) // 4
    for i, (num, lab) in enumerate(NUMBERS):
        x = M + i * (nbox + 10)
        cv.rect(x, y, nbox, 52, LIGHT)
        cv.rect(x, y, nbox, 3, GOLD)
        cv.text_center(x + nbox // 2, y + 8, num, NAVY, 2)
        for j, ln in enumerate(cv.wrap(lab, nbox - 12, 1)):
            cv.text_center(x + nbox // 2, y + 30 + j * 10, ln, (60, 60, 55), 1)
    y += 52 + 10
    cv.hline(M, y, W - 2 * M, INK, 2)
    y += 8
    # ---- timeline ----
    cv.text(M, y, "THROUGH THE DAY  ·  UTC", RED, 2)
    y += 22
    ty = y + 8
    cv.hline(M + 4, ty, W - 2 * M - 8, LINE, 2)
    tcol = (W - 2 * M) // 6
    for i, (t, txt) in enumerate(TIMELINE):
        x = M + i * tcol
        cv.circle(x + 8, ty, 5, RED)
        cv.text(x, ty + 10, t, NAVY, 1)
        for j, ln in enumerate(cv.wrap(txt, tcol - 10, 1)[:3]):
            cv.text(x, ty + 22 + j * 10, ln, (60, 60, 55), 1)
    y = ty + 56
    cv.hline(M, y, W - 2 * M, INK, 2)
    y += 8
    # ---- briefs ----
    cv.text(M, y, "ALSO ON 19 NOVEMBER  —  %d MORE STORIES" % len(BRIEFS), RED, 2)
    y += 22
    bcol = (W - 2 * M - 2 * 12) // 3
    per = (len(BRIEFS) + 2) // 3
    for ci in range(3):
        x = M + ci * (bcol + 12)
        for ri in range(per):
            idx = ci * per + ri
            if idx >= len(BRIEFS):
                break
            by = y + ri * 15
            item = "%d. %s" % (idx + 13, BRIEFS[idx])
            # truncate to column width
            while cv.text_w(item, 1) > bcol and len(item) > 4:
                item = item[:-4] + "..."
            cv.text(x, by, item, INK, 1)
    y += per * 15 + 6
    # ---- footer ----
    cv.hline(M, y, W - 2 * M, INK, 2)
    y += 8
    cv.text(M, y, "SOURCES: REUTERS, AP, AFP, BBC, AL JAZEERA, CNN, FT, UN, IAEA, ICJ.",
            (60, 60, 55), 1)
    y += 11
    cv.text(M, y, "ALL STORIES HAPPENED OR WERE FIRST REPORTED ON 19 NOVEMBER 2026. "
                  "DISPUTED CLAIMS ARE ATTRIBUTED.", (60, 60, 55), 1)
    data = png_bytes(cv)
    with open(out_path, 'wb') as f:
        f.write(data)
    return len(data)


if __name__ == '__main__':
    out = os.environ.get('MAKEFUN_OUTPUT_DIR', 'out')
    os.makedirs(out, exist_ok=True)
    n = build(os.path.join(out, 'entry.png'))
    print('wrote %d bytes' % n)
