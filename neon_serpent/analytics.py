"""
analytics.py
Data Analytics screen — single-session focus, 4 graphs + KPI cards.

Layout
------
[ < ]  Session N / 3  [ > ]                                [ BACK ]
┌────────────────────────────────────────────────────────────┐
│  KPI: SURVIVED · ACCURACY · KILLS · DEATHS                 │
├────────────────────────────────────────────────────────────┤
│       Performance Timeline (HP + Kills + level bands)      │
├──────────────────┬──────────────────┬──────────────────────┤
│ Shooting Pattern │ Movement Heatmap │  Damage Balance      │
│   (histogram)    │    (scatter)     │  (stacked area)      │
└──────────────────┴──────────────────┴──────────────────────┘
"""
from __future__ import annotations
import math
import pygame
from .constants import W, H, C_BG, C_WHITE, C_DIM, C_HUD_BORDER, C_GOLD, get_fonts

# ── Visual constants ──────────────────────────────────────────────────────────
PAD             = 24
TITLE_H         = 70
KPI_H           = 80
TIMELINE_H      = 270
SMALL_H         = 280
BTN_H           = 44

C_HP            = (255, 60, 96)
C_KILLS         = (80, 255, 120)
C_ACCURACY      = (0, 200, 255)
C_DEATHS        = (255, 180, 0)
C_DEALT         = (80, 255, 120)
C_TAKEN         = (255, 80, 80)
C_LEVEL_BAND    = [(20, 30, 50), (30, 25, 60), (50, 15, 50)]   # subtle level tint

MAX_LIVES       = 10
MAX_HP_PER_LIFE = 3
MAX_HEALTH      = 33    # (lives 10 × hp 3 + hp 3)


# ── UI rectangles ─────────────────────────────────────────────────────────────
BACK_BTN     = pygame.Rect(W - 140, 14, 120, 36)
PREV_BTN     = pygame.Rect(20, 14, 60, 36)
NEXT_BTN     = pygame.Rect(0, 14, 60, 36)   # x set dynamically
# Timeline scroll buttons (x updated each draw)
TL_PREV_BTN  = pygame.Rect(0, 0, 30, 26)
TL_NEXT_BTN  = pygame.Rect(0, 0, 30, 26)
TIMELINE_WINDOW_S  = 60   # show 60 seconds at a time
TIMELINE_SCROLL_S  = 20   # step each click


# ── Helpers ───────────────────────────────────────────────────────────────────

def _to_int(s, default=0):
    try:    return int(float(s))
    except: return default

def _session_outcome(rows: list[dict]) -> tuple[str, str]:
    """
    Return (outcome, cause).
    outcome ∈ {"WIN", "LOST"}.  cause = "" for WIN, death cause for LOST.
    Default to LOST with empty cause if no event found.
    """
    for r in rows:
        ev = r.get("event", "")
        if ev == "victory":
            return ("WIN", "")
        if ev.startswith("game_over"):
            # Format: "game_over:CAUSE_TEXT"
            cause = ev.split(":", 1)[1] if ":" in ev else ""
            return ("LOST", cause)
    return ("LOST", "")


def _session_label(idx_from_latest: int) -> str:
    """0 → 'Latest session', 1 → '1 session ago', ..."""
    if idx_from_latest == 0:
        return "Latest session"
    if idx_from_latest == 1:
        return "1 session ago"
    return f"{idx_from_latest} sessions ago"



def _map(v, lo, hi, out_lo, out_hi):
    if hi == lo:
        return out_lo
    return out_lo + (v - lo) / (hi - lo) * (out_hi - out_lo)


def _panel(surf, rect, title, subtitle, fonts):
    pygame.draw.rect(surf, (10, 14, 28), rect, border_radius=8)
    pygame.draw.rect(surf, (40, 70, 110), rect, 1, border_radius=8)
    surf.blit(fonts["sm"].render(title, True, C_WHITE), (rect.x + 12, rect.y + 8))
    if subtitle:
        st = fonts["sm"].render(subtitle, True, C_DIM)
        surf.blit(st, (rect.x + rect.w - st.get_width() - 10, rect.y + 8))


def _axes(surf, inner):
    col = (50, 70, 110)
    pygame.draw.line(surf, col, (inner.x, inner.y), (inner.x, inner.bottom), 1)
    pygame.draw.line(surf, col, (inner.x, inner.bottom), (inner.right, inner.bottom), 1)


def _inner(rect, lpad=64, rpad=28, tpad=62, bpad=92):
    return pygame.Rect(rect.x + lpad, rect.y + tpad,
                       rect.w - lpad - rpad, rect.h - tpad - bpad)


# ── KPI Cards ─────────────────────────────────────────────────────────────────

def _draw_kpi(surf, x, y, w, h, label, value, color, fonts, subtitle=""):
    pygame.draw.rect(surf, (10, 14, 28), (x, y, w, h), border_radius=10)
    pygame.draw.rect(surf, color, (x, y, w, h), 1, border_radius=10)
    # Side accent bar
    pygame.draw.rect(surf, color, (x, y, 4, h), border_radius=2)
    # Label (small, dim)
    lbl_t = fonts["sm"].render(label, True, C_DIM)
    surf.blit(lbl_t, (x + 14, y + 10))
    # Value (large, bright)
    big   = pygame.font.SysFont("consolas", 32, bold=True)
    val_t = big.render(value, True, color)
    surf.blit(val_t, (x + 14, y + 30))
    # Subtitle (small, same colour as value but dimmer)
    if subtitle:
        # Truncate to fit card width
        max_chars = max(8, (w - 28) // 8)
        st = subtitle if len(subtitle) <= max_chars else subtitle[:max_chars - 1] + "…"
        st_t = fonts["sm"].render(st, True, color)
        surf.blit(st_t, (x + 14, y + h - 22))


def _draw_kpis(surf, rows: list[dict], fonts) -> None:
    """5 KPI cards across the top of the dashboard."""
    if rows:
        survived = max(_to_int(r["t"]) for r in rows)
        kills    = sum(_to_int(r["kills"]) for r in rows)
        shots    = sum(_to_int(r["shots"]) for r in rows)
        hits     = sum(_to_int(r["hits"])  for r in rows)
        # DEATHS = lives lost = initial_lives - min(lives)
        # snake starts at MAX_LIVES = 10
        min_lives = min(_to_int(r["lives"]) for r in rows) if rows else MAX_LIVES
        deaths   = max(0, MAX_LIVES - min_lives)
        acc      = min(100, round(hits / max(shots, 1) * 100))   # clamp 100%
        outcome, cause = _session_outcome(rows)
    else:
        survived = kills = deaths = 0
        acc      = 0
        outcome, cause = "—", ""

    if outcome == "WIN":
        outcome_col = (80, 255, 120)
    elif outcome == "LOST":
        outcome_col = (255, 80, 100)
    else:
        outcome_col = C_DIM

    # Subtitle only for LOST (death cause)
    outcome_sub = cause if outcome == "LOST" else ""

    cards = [
        ("OUTCOME",   outcome,        outcome_col, outcome_sub),
        ("SURVIVED",  f"{survived}s", C_HUD_BORDER, ""),
        ("ACCURACY",  f"{acc}%",      C_ACCURACY,  ""),
        ("KILLS",     str(kills),     C_KILLS,     ""),
        ("DEATHS",    str(deaths),    C_DEATHS,    ""),
    ]
    card_w = (W - PAD * 6) // 5
    for i, (lbl, val, col, sub) in enumerate(cards):
        cx = PAD + i * (card_w + PAD)
        cy = TITLE_H
        _draw_kpi(surf, cx, cy, card_w, KPI_H, lbl, val, col, fonts, subtitle=sub)


# ── Performance Timeline ─────────────────────────────────────────────────────

def _draw_timeline(surf, rect, rows, fonts, scroll_offset: int = 0) -> None:
    _panel(surf, rect, "Performance Timeline", "", fonts)
    # Legend strip below title
    legend_y = rect.y + 28
    legend_x = rect.x + 14
    legend_items = [
        ("HP / Lives",    C_HP,            "line"),
        ("Kills",         C_KILLS,         "line"),
        ("Lost life",     (255, 80, 80),   "marker"),
        ("Key collected", (255, 220, 0),   "marker"),
        ("Ammo pickup",   (0, 200, 255),   "marker"),
        ("Missile hit",   (255, 160, 0),   "marker"),
    ]
    for label, col, kind in legend_items:
        if kind == "line":
            pygame.draw.line(surf, col, (legend_x, legend_y + 7),
                             (legend_x + 20, legend_y + 7), 2)
        else:
            pygame.draw.polygon(surf, col, [
                (legend_x + 4,  legend_y + 12),
                (legend_x + 14, legend_y + 12),
                (legend_x + 9,  legend_y + 4),
            ])
        lt = fonts["sm"].render(label, True, C_WHITE)
        surf.blit(lt, (legend_x + 26, legend_y + 1))
        legend_x += 26 + lt.get_width() + 18
    inner = _inner(rect, lpad=72, rpad=72, tpad=70, bpad=58)
    _axes(surf, inner)

    if not rows:
        return

    # Full session time range — no scrolling
    t_max = max(_to_int(r["t"]) for r in rows) or 1
    TL_PREV_BTN.update(0, 0, 0, 0)
    TL_NEXT_BTN.update(0, 0, 0, 0)

    # ── Level bands (background tint) ─────────────────────────────────────────
    prev_lv = _to_int(rows[0]["level"])
    band_start = 0
    bands = []   # (level, t0, t1)
    for r in rows:
        lv = _to_int(r["level"])
        t  = _to_int(r["t"])
        if lv != prev_lv:
            bands.append((prev_lv, band_start, t))
            band_start = t
            prev_lv    = lv
    bands.append((prev_lv, band_start, t_max))

    for idx, (lv, t0, t1) in enumerate(bands):
        x0 = int(_map(t0, 0, t_max, inner.x, inner.right))
        x1 = int(_map(t1, 0, t_max, inner.x, inner.right))
        col = C_LEVEL_BAND[min(lv - 1, len(C_LEVEL_BAND) - 1)]
        pygame.draw.rect(surf, col, (x0, inner.y, x1 - x0, inner.h))
        # Vertical dashed divider at start of each band (except first)
        if idx > 0:
            for yy in range(inner.y, inner.bottom, 8):
                pygame.draw.line(surf, (200, 200, 220),
                                 (x0, yy), (x0, yy + 4), 1)

    # Re-draw axes on top of bands
    _axes(surf, inner)

    # ── Y left: HP gridlines (lives boundaries) ──────────────────────────────
    MAX_LIVES = 10
    MAX_HP    = 3
    for lives_v in range(0, MAX_LIVES + 1):
        y = int(_map(lives_v * MAX_HP, 0, MAX_HEALTH, inner.bottom, inner.y))
        pygame.draw.line(surf, (35, 50, 80), (inner.x, y), (inner.right, y), 1)
        if lives_v % 2 == 0:
            lt = fonts["sm"].render(str(lives_v), True, C_WHITE)
            surf.blit(lt, (inner.x - lt.get_width() - 6, y - lt.get_height() // 2))

    # Y left header
    yl_l = fonts["sm"].render("LIVES", True, C_HP)
    surf.blit(yl_l, (inner.x - 42, inner.y - 26))

    # ── HP timeline (red line) ───────────────────────────────────────────────
    pts_hp = []
    for r in rows:
        t  = _to_int(r["t"])
        h  = _to_int(r["lives"]) * MAX_HP + _to_int(r["hp"])
        px = int(_map(t, 0, t_max, inner.x, inner.right))
        py = int(_map(h, 0, MAX_HEALTH, inner.bottom, inner.y))
        pts_hp.append((px, py))
    if len(pts_hp) >= 2:
        pygame.draw.lines(surf, C_HP, False, pts_hp, 2)

    # ── Cumulative kills (green line, right axis) ────────────────────────────
    cum_kills = []
    total = 0
    for r in rows:
        total += _to_int(r["kills"])
        cum_kills.append(total)
    max_k = max(cum_kills) if cum_kills else 1
    max_k = max(max_k, 1)

    # Right Y ticks
    for i in range(0, 5):
        v = int(max_k * i / 4)
        y = int(_map(v, 0, max_k, inner.bottom, inner.y))
        kt = fonts["sm"].render(str(v), True, C_WHITE)
        surf.blit(kt, (inner.right + 6, y - kt.get_height() // 2))
    yl_r = fonts["sm"].render("KILLS", True, C_KILLS)
    surf.blit(yl_r, (inner.right + 4, inner.y - 26))

    pts_k = []
    for r, k in zip(rows, cum_kills):
        t  = _to_int(r["t"])
        px = int(_map(t, 0, t_max, inner.x, inner.right))
        py = int(_map(k, 0, max_k, inner.bottom, inner.y))
        pts_k.append((px, py))
    if len(pts_k) >= 2:
        pygame.draw.lines(surf, C_KILLS, False, pts_k, 2)

    # ── Event markers ────────────────────────────────────────────────────────
    for r in rows:
        ev = r.get("event", "")
        if not ev:
            continue
        t  = _to_int(r["t"])
        px = int(_map(t, 0, t_max, inner.x, inner.right))
        # Vertical dashed line
        for yy in range(inner.y, inner.bottom, 6):
            pygame.draw.line(surf, (255, 200, 80), (px, yy), (px, yy + 3), 1)
        # Marker icon at top
        icon_col = {
            "lost_life":     (255, 80,  80),
            "key_collected": (255, 220, 0),
            "ammo_collected":(0,  200, 255),
            "missile_hit":   (255, 160, 0),
        }.get(ev, (200, 200, 200))
        pygame.draw.polygon(surf, icon_col, [
            (px - 5, inner.y - 8),
            (px + 5, inner.y - 8),
            (px,     inner.y - 2),
        ])

    # ── Prominent level labels (drawn LAST so they sit on top) ──────────────
    bold_fnt = pygame.font.SysFont("consolas", 18, bold=True)
    for lv, t0, t1 in bands:
        x0 = int(_map(t0, 0, t_max, inner.x, inner.right))
        lvl_name = "BOSS" if lv >= 3 else f"LEVEL {lv}"
        lvl_col  = (255, 80, 80) if lv >= 3 else C_WHITE
        lvl_lbl  = bold_fnt.render(lvl_name, True, lvl_col)
        surf.blit(lvl_lbl, (x0 + 6, inner.y + 4))

    # X-axis time ticks — auto step, labels clamped within inner bounds
    tick_step = 10 if t_max <= 60 else (30 if t_max <= 180 else 60)
    t_tick = tick_step
    while t_tick <= t_max:
        x_t = int(_map(t_tick, 0, t_max, inner.x, inner.right))
        pygame.draw.line(surf, (60, 80, 110), (x_t, inner.bottom), (x_t, inner.bottom + 4), 1)
        lbl = f"{t_tick}"
        tt  = fonts["sm"].render(lbl, True, C_WHITE)
        # Clamp so label never overflows left/right edge
        lx  = max(inner.x, min(x_t - tt.get_width() // 2, inner.right - tt.get_width()))
        surf.blit(tt, (lx, inner.bottom + 6))
        t_tick += tick_step
    # X axis title
    xl = fonts["sm"].render("time (s)", True, C_WHITE)
    surf.blit(xl, (inner.centerx - xl.get_width() // 2, inner.bottom + 30))


# ── Graph A: Shooting Pattern (Histogram) ────────────────────────────────────

def _draw_shooting(surf, rect, rows, fonts) -> None:
    """Bar graph: shots per 20-second window."""
    _panel(surf, rect, "A · Shooting Activity", "", fonts)
    inner = _inner(rect)
    _axes(surf, inner)

    if not rows:
        return

    WINDOW = 20  # seconds
    t_max  = max(_to_int(r["t"]) for r in rows) or 1
    n_bins = max(1, (t_max // WINDOW) + 1)
    bins   = [0] * n_bins
    for r in rows:
        t   = _to_int(r["t"])
        sh  = _to_int(r["shots"])
        idx = min(t // WINDOW, n_bins - 1)
        bins[idx] += sh

    max_c = max(max(bins), 1)

    # Y ticks
    for i in range(5):
        v = int(max_c * i / 4)
        y = int(_map(v, 0, max_c, inner.bottom, inner.y))
        pygame.draw.line(surf, (40, 55, 85), (inner.x, y), (inner.right, y), 1)
        lt = fonts["sm"].render(str(v), True, C_WHITE)
        surf.blit(lt, (inner.x - lt.get_width() - 4, y - lt.get_height() // 2))

    # Bars (no X label inside loop)
    bar_w_avail = inner.w / n_bins
    bar_w = max(6, int(bar_w_avail * 0.75))
    for i, c in enumerate(bins):
        cx = int(_map(i + 0.5, 0, n_bins, inner.x, inner.right))
        bx = cx - bar_w // 2
        bh = int(_map(c, 0, max_c, 0, inner.h))
        by = inner.bottom - bh
        if bh > 0:
            pygame.draw.rect(surf, C_ACCURACY, (bx, by, bar_w, bh), border_radius=3)
            pygame.draw.rect(surf, (160, 220, 255), (bx, by, bar_w, bh), 1, border_radius=3)
    # X tick marks every bin (20s), labels every 2nd bin to avoid crowding
    step_label = 1 if n_bins <= 8 else 2
    for i in range(1, n_bins + 1):   # start at 1 → skip 0s
        bx_edge = int(_map(i, 0, n_bins, inner.x, inner.right))
        # Tick mark every 20s (every bin)
        pygame.draw.line(surf, C_WHITE, (bx_edge, inner.bottom),
                         (bx_edge, inner.bottom + 4), 1)
        # Label only every step_label-th bin
        if i % step_label == 0 and i < n_bins + 1:
            lbl = f"{i*WINDOW}s"
            lt  = fonts["sm"].render(lbl, True, C_WHITE)
            lx  = max(inner.x, min(bx_edge - lt.get_width() // 2,
                                    inner.right - lt.get_width()))
            surf.blit(lt, (lx, inner.bottom + 6))
    # X-axis label
    axl = fonts["sm"].render("time (s)", True, C_WHITE)
    surf.blit(axl, (inner.centerx - axl.get_width() // 2, inner.bottom + 30))
    # Y-axis label
    ayl = fonts["sm"].render("shots fired", True, C_WHITE)
    surf.blit(ayl, (inner.x - 8, inner.y - 22))
    # Subtitle below graph
    sub_t = fonts["sm"].render("X: time window  ·  Y: total shots fired", True, C_DIM)
    surf.blit(sub_t, (rect.x + 12, rect.bottom - sub_t.get_height() - 8))


# ── Graph B: Movement Heatmap ────────────────────────────────────────────────

def _draw_heatmap(surf, rect, rows, fonts) -> None:
    _panel(surf, rect, "B · Movement Heatmap", "", fonts)
    # Use same generous bpad as other graphs so axis label + subtitle fit
    inner = _inner(rect, lpad=20, rpad=14, tpad=44, bpad=70)
    pygame.draw.rect(surf, (4, 6, 14), inner)

    WORLD_W, WORLD_H = 1400, 800
    dot_surf = pygame.Surface((inner.w, inner.h), pygame.SRCALPHA)
    for r in rows:
        try:
            px = int(_map(_to_int(r["pos_x"]), 0, WORLD_W, 0, inner.w))
            py = int(_map(_to_int(r["pos_y"]), 0, WORLD_H, 0, inner.h))
            px = max(0, min(inner.w - 1, px))
            py = max(0, min(inner.h - 1, py))
            pygame.draw.circle(dot_surf, (0, 220, 255, 70), (px, py), 4)
        except (ValueError, KeyError):
            continue
    surf.blit(dot_surf, (inner.x, inner.y))

    # Frame
    pygame.draw.rect(surf, (40, 70, 110), inner, 1)
    # Corner labels showing world coords range
    tl = fonts["sm"].render("(0, 0)", True, C_WHITE)
    br = fonts["sm"].render(f"({WORLD_W}, {WORLD_H})", True, C_WHITE)
    surf.blit(tl, (inner.x + 4, inner.y + 4))
    surf.blit(br, (inner.right - br.get_width() - 4, inner.bottom - br.get_height() - 4))
    # Axis label (just below frame)
    axl = fonts["sm"].render("snake position (x, y)", True, C_WHITE)
    surf.blit(axl, (inner.centerx - axl.get_width() // 2, inner.bottom + 8))
    # Subtitle at bottom of panel
    sub_t = fonts["sm"].render("X: world X  ·  Y: world Y  ·  density = time", True, C_DIM)
    surf.blit(sub_t, (rect.x + 12, rect.bottom - sub_t.get_height() - 8))


# ── Graph C: Damage Balance (Stacked area) ───────────────────────────────────

def _draw_damage(surf, rect, rows, fonts) -> None:
    """Stacked area: red (taken) on bottom, green (dealt) stacked above. 10s windows."""
    # Draw panel + custom subtitle with colour swatches
    pygame.draw.rect(surf, (10, 14, 28), rect, border_radius=8)
    pygame.draw.rect(surf, (40, 70, 110), rect, 1, border_radius=8)
    surf.blit(fonts["sm"].render("C · Damage Balance", True, C_WHITE),
              (rect.x + 12, rect.y + 8))

    inner = _inner(rect)
    _axes(surf, inner)

    if not rows:
        return

    # Aggregate into 10s windows
    WINDOW = 10
    t_max  = max(_to_int(r["t"]) for r in rows) or 1
    n_bins = max(1, (t_max // WINDOW) + 1)
    dealt_w  = [0] * n_bins
    taken_w  = [0] * n_bins
    for r in rows:
        t   = _to_int(r["t"])
        idx = min(t // WINDOW, n_bins - 1)
        dealt_w[idx] += _to_int(r["dmg_dealt"])
        taken_w[idx] += _to_int(r["dmg_taken"])

    # Auto-scale Y axis: max(dealt+taken) across windows
    max_v = max((d + t) for d, t in zip(dealt_w, taken_w)) or 1
    # Round up to nice number (multiple of 5 or 10)
    if max_v <= 10:
        max_v = 10
    elif max_v <= 20:
        max_v = 20
    elif max_v <= 50:
        max_v = ((max_v + 9) // 10) * 10
    else:
        max_v = ((max_v + 19) // 20) * 20

    # Y ticks
    for i in range(5):
        v = int(max_v * i / 4)
        y = int(_map(v, 0, max_v, inner.bottom, inner.y))
        pygame.draw.line(surf, (40, 55, 85), (inner.x, y), (inner.right, y), 1)
        lt = fonts["sm"].render(str(v), True, C_WHITE)
        surf.blit(lt, (inner.x - lt.get_width() - 4, y - lt.get_height() // 2))

    # ── Level bands ──
    # Determine level transitions from rows
    prev_lv = _to_int(rows[0]["level"])
    band_start_t = 0
    bands = []
    for r in rows:
        lv = _to_int(r["level"])
        t  = _to_int(r["t"])
        if lv != prev_lv:
            bands.append((prev_lv, band_start_t, t))
            band_start_t = t
            prev_lv = lv
    bands.append((prev_lv, band_start_t, t_max))

    for idx, (lv, t0, t1) in enumerate(bands):
        x0 = int(_map(t0, 0, t_max, inner.x, inner.right))
        x1 = int(_map(t1, 0, t_max, inner.x, inner.right))
        col = C_LEVEL_BAND[min(lv - 1, len(C_LEVEL_BAND) - 1)]
        band_surf = pygame.Surface((x1 - x0, inner.h), pygame.SRCALPHA)
        band_surf.fill((*col, 140))
        surf.blit(band_surf, (x0, inner.y))
        if idx > 0:
            for yy in range(inner.y, inner.bottom, 8):
                pygame.draw.line(surf, (200, 200, 220),
                                 (x0, yy), (x0, yy + 4), 1)
        lvl_name = "BOSS" if lv >= 3 else f"L{lv}"
        lvl_lbl = fonts["sm"].render(lvl_name, True, C_WHITE)
        surf.blit(lvl_lbl, (x0 + 4, inner.y + 2))

    _axes(surf, inner)

    # ── Build smooth stacked area polygons (line connecting bin endpoints) ──
    # X positions: 0 at inner.x, then end-of-bin (i+1)*WINDOW seconds
    # So point i corresponds to t = i * WINDOW seconds, value taken_w[i-1] / dealt_w[i-1]
    # Effectively: x = _map(i*WINDOW, 0, t_max, inner.x, inner.right)

    # Sample points: one per bin endpoint, plus origin (0, 0)
    n_points = n_bins + 1   # 0, 10s, 20s, ..., n_bins*10s
    sample_t = [i * WINDOW for i in range(n_points)]
    # Values at each point: bin (i-1) for i>=1, both 0 at i=0
    taken_pt = [0] + list(taken_w)
    dealt_pt = [0] + list(dealt_w)

    def x_at(t):
        return int(_map(t, 0, n_bins * WINDOW, inner.x, inner.right))

    # Taken polygon (red, bottom — anchored on baseline)
    pts_taken = [(inner.x, inner.bottom)]
    for t, v in zip(sample_t, taken_pt):
        x = x_at(t)
        y = int(_map(v, 0, max_v, inner.bottom, inner.y))
        pts_taken.append((x, y))
    pts_taken.append((x_at(sample_t[-1]), inner.bottom))
    if len(pts_taken) >= 3:
        ts = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.polygon(ts, (*C_TAKEN, 220), pts_taken)
        surf.blit(ts, (0, 0))

    # Dealt polygon (green, stacked above taken)
    pts_dealt_top    = []
    pts_dealt_bottom = []
    for t, d, tk in zip(sample_t, dealt_pt, taken_pt):
        x = x_at(t)
        y_taken = int(_map(tk, 0, max_v, inner.bottom, inner.y))
        y_total = int(_map(tk + d, 0, max_v, inner.bottom, inner.y))
        pts_dealt_bottom.append((x, y_taken))
        pts_dealt_top.append((x, y_total))
    pts_dealt = pts_dealt_bottom + list(reversed(pts_dealt_top))
    if len(pts_dealt) >= 3:
        ds = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.polygon(ds, (*C_DEALT, 220), pts_dealt)
        surf.blit(ds, (0, 0))

    # Outline strokes for clarity
    if len(pts_dealt_top) >= 2:
        pygame.draw.lines(surf, C_DEALT, False, pts_dealt_top, 2)
    if len(pts_dealt_bottom) >= 2:
        pygame.draw.lines(surf, C_TAKEN, False, pts_dealt_bottom, 2)

    # ── X tick marks every 10s (every bin); labels every 4 bins ──
    label_step = 4
    for i in range(1, n_bins + 1):
        t_at_tick = i * WINDOW
        bx_edge   = x_at(t_at_tick)
        # Always draw tick mark
        pygame.draw.line(surf, C_WHITE, (bx_edge, inner.bottom),
                         (bx_edge, inner.bottom + 4), 1)
        # Label only every 4th bin
        if i % label_step == 0:
            lbl = f"{t_at_tick}s"
            lt  = fonts["sm"].render(lbl, True, C_WHITE)
            lx  = max(inner.x, min(bx_edge - lt.get_width() // 2,
                                    inner.right - lt.get_width()))
            surf.blit(lt, (lx, inner.bottom + 6))

    # X label
    xl = fonts["sm"].render("time (s)", True, C_WHITE)
    surf.blit(xl, (inner.centerx - xl.get_width() // 2, inner.bottom + 30))
    # Y label
    yl = fonts["sm"].render("damage", True, C_WHITE)
    surf.blit(yl, (inner.x - 8, inner.y - 22))
    # Subtitle below graph (with swatches)
    sub_x = rect.x + 12
    sub_y = rect.bottom - 22
    pre_t = fonts["sm"].render("X: time (10s)  ·  Y: dmg  ", True, C_DIM)
    surf.blit(pre_t, (sub_x, sub_y))
    sub_x += pre_t.get_width()
    pygame.draw.rect(surf, C_DEALT, (sub_x, sub_y + 2, 10, 10), border_radius=2)
    sub_x += 14
    surf.blit(fonts["sm"].render("dealt", True, C_DIM), (sub_x, sub_y))
    sub_x += fonts["sm"].size("dealt")[0] + 8
    pygame.draw.rect(surf, C_TAKEN, (sub_x, sub_y + 2, 10, 10), border_radius=2)
    sub_x += 14
    surf.blit(fonts["sm"].render("taken", True, C_DIM), (sub_x, sub_y))


# ── Public draw ──────────────────────────────────────────────────────────────

def draw_analytics(
    surf: pygame.Surface,
    sessions: dict,
    selected_sid: int,
    btn_back_hover: bool = False,
    btn_prev_hover: bool = False,
    btn_next_hover: bool = False,
    timeline_scroll_offset: int = 0,
) -> None:
    """
    Render the analytics dashboard for a single selected session.

    Parameters
    ----------
    sessions     : {session_id: [rows]} from StatsTracker.load_sessions()
    selected_sid : currently displayed session id
    """
    fonts = get_fonts()
    surf.fill(C_BG)

    sids = sorted(sessions.keys())

    # ── Title bar ──
    title = fonts["med"].render("DATA ANALYTICS", True, C_HUD_BORDER)
    surf.blit(title, (W // 2 - title.get_width() // 2, 16))

    # Session selector
    if sids:
        cur_idx = sids.index(selected_sid) if selected_sid in sids else 0

        # Prev button
        prev_col = (0, 200, 255) if btn_prev_hover else (50, 80, 120)
        pygame.draw.rect(surf, (12, 18, 32), PREV_BTN, border_radius=6)
        pygame.draw.rect(surf, prev_col, PREV_BTN, 1, border_radius=6)
        pt = fonts["mono"].render("<", True, prev_col)
        surf.blit(pt, (PREV_BTN.centerx - pt.get_width() // 2,
                       PREV_BTN.centery - pt.get_height() // 2))

        # Session label: "Latest session" / "N sessions ago" + outcome badge
        from_latest = len(sids) - 1 - cur_idx
        sess_text   = _session_label(from_latest)
        rows_for_outcome = sessions.get(selected_sid, [])
        outcome, _cause  = _session_outcome(rows_for_outcome)
        if outcome == "WIN":
            oc_col = (80, 255, 120)
        elif outcome == "LOST":
            oc_col = (255, 80, 100)
        else:
            oc_col = C_DIM
        sl1 = fonts["mono"].render(sess_text, True, C_WHITE)
        sl2 = fonts["mono"].render(f"  •  {outcome}", True, oc_col)
        sl3 = fonts["sm"].render(f"({cur_idx + 1}/{len(sids)})", True, C_DIM)
        surf.blit(sl1, (PREV_BTN.right + 16, 16))
        surf.blit(sl2, (PREV_BTN.right + 16 + sl1.get_width(), 16))
        surf.blit(sl3, (PREV_BTN.right + 16, 38))

        # Next button (placed after label)
        label_w    = sl1.get_width() + sl2.get_width() + 16
        NEXT_BTN.x = PREV_BTN.right + 16 + label_w
        next_col = (0, 200, 255) if btn_next_hover else (50, 80, 120)
        pygame.draw.rect(surf, (12, 18, 32), NEXT_BTN, border_radius=6)
        pygame.draw.rect(surf, next_col, NEXT_BTN, 1, border_radius=6)
        nt = fonts["mono"].render(">", True, next_col)
        surf.blit(nt, (NEXT_BTN.centerx - nt.get_width() // 2,
                       NEXT_BTN.centery - nt.get_height() // 2))

    # Back button (top right)
    back_col = (0, 200, 255) if btn_back_hover else (50, 80, 120)
    pygame.draw.rect(surf, (12, 18, 32), BACK_BTN, border_radius=6)
    pygame.draw.rect(surf, back_col, BACK_BTN, 1, border_radius=6)
    bt = fonts["mono"].render("[ BACK ]", True, back_col)
    surf.blit(bt, (BACK_BTN.centerx - bt.get_width() // 2,
                   BACK_BTN.centery - bt.get_height() // 2))

    if not sessions:
        msg = fonts["med"].render("No data yet — play a game first!", True, C_DIM)
        surf.blit(msg, (W // 2 - msg.get_width() // 2, H // 2 - 20))
        return

    rows = sessions.get(selected_sid, [])

    # ── KPI cards ──
    _draw_kpis(surf, rows, fonts)

    # ── Performance Timeline ──
    tl_y = TITLE_H + KPI_H + PAD
    tl_rect = pygame.Rect(PAD, tl_y, W - PAD * 2, TIMELINE_H)
    _draw_timeline(surf, tl_rect, rows, fonts, scroll_offset=timeline_scroll_offset)

    # ── 3 small graphs ──
    sg_y = tl_y + TIMELINE_H + PAD
    sg_w = (W - PAD * 4) // 3
    rect_a = pygame.Rect(PAD,                    sg_y, sg_w, SMALL_H)
    rect_b = pygame.Rect(PAD * 2 + sg_w,         sg_y, sg_w, SMALL_H)
    rect_c = pygame.Rect(PAD * 3 + sg_w * 2,     sg_y, sg_w, SMALL_H)

    _draw_shooting(surf, rect_a, rows, fonts)
    _draw_heatmap(surf, rect_b, rows, fonts)
    _draw_damage(surf, rect_c, rows, fonts)