"""
hud.py
All overlay / screen-rendering functions.

HUD layout (left → right, taller bar = 72 px):
  [12]  HP pips  [divider]  Heart lives + immortal arc  [divider]  AMMO  [divider]  KEYS  [divider]  DASH  [right edge]  TIME / KILLS / LEVEL
"""
import math
import pygame
from .constants import (
    W, H,
    C_BG, C_SNAKE_H, C_SNAKE_I, C_AMMO, C_KEY, C_EXIT,
    C_HUD_BORDER, C_BOSS,
    C_RED, C_GOLD, C_WHITE, C_DIM,
    get_fonts,
)
from .renderer import draw_glowing_rect, draw_health_bar

HUD_H = 44   # total HUD bar height


# ═══════════════════════════════════════════════════════════════════════════════
# Internal drawing helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _vdivider(surf: pygame.Surface, x: int) -> None:
    """Thin vertical separator line inside the HUD."""
    pygame.draw.line(surf, (40, 60, 100), (x, 3), (x, HUD_H - 3), 1)


def _section_label(surf: pygame.Surface, text: str, x: int, fonts: dict) -> None:
    t = fonts["sm"].render(text, True, C_WHITE)
    surf.blit(t, (x, 2))


# ── HP pips ──────────────────────────────────────────────────────────────────

def _draw_hp(surf: pygame.Surface, snake, x: int, fonts: dict) -> int:
    """
    Draw HP as filled/empty square pips.
    Returns the x coordinate of the right edge of this section.
    """
    _section_label(surf, "HP", x, fonts)

    pip_w, pip_h = 18, 18
    gap          = 5
    cy           = HUD_H // 2 + 2

    for i in range(snake.max_hp):
        px = x + i * (pip_w + gap)
        py = cy - pip_h // 2

        if i < snake.hp:
            # filled pip with green glow
            pygame.draw.rect(surf, (0, 180, 80),  (px, py, pip_w, pip_h), border_radius=4)
            pygame.draw.rect(surf, (0, 255, 120), (px, py, pip_w, pip_h), 2, border_radius=4)
        else:
            # empty pip
            pygame.draw.rect(surf, (15, 30, 15),  (px, py, pip_w, pip_h), border_radius=4)
            pygame.draw.rect(surf, (30, 60, 30),  (px, py, pip_w, pip_h), 1, border_radius=4)

    return x + snake.max_hp * (pip_w + gap) - gap


# ── Heart lives ───────────────────────────────────────────────────────────────

def _draw_heart(surf: pygame.Surface, cx: int, cy: int, size: int,
                color: tuple, alpha: int = 255) -> None:
    """
    Pixel-perfect heart: two circles (top lobes) + filled triangle (bottom point).
    size = lobe radius.
    """
    s = pygame.Surface((size * 4 + 2, size * 4 + 2), pygame.SRCALPHA)
    r = size
    pygame.draw.circle(s, (*color, alpha), (r,         r), r)
    pygame.draw.circle(s, (*color, alpha), (r * 3,     r), r)
    pts = [(0, r), (r * 4, r), (r * 2, r * 4 - 1)]
    pygame.draw.polygon(s, (*color, alpha), pts)
    surf.blit(s, (cx - r * 2, cy - r))


def _draw_lives(surf: pygame.Surface, snake, x: int, fonts: dict) -> int:
    """
    Draw 5 heart icons.
    - Full hearts  → bright red + soft glow
    - Empty hearts → dark hollow
    - While life-immortal: flashing cyan arc around next-empty slot + timer text.
    Returns right-edge x.
    """
    now      = pygame.time.get_ticks()
    size     = 5            # lobe radius (half) → heart ~20 wide × 21 tall
    spacing  = 26
    col_full = (230,  30,  60)
    col_empty= ( 50,  10,  20)
    col_glow = (255,  80, 120)

    _section_label(surf, "LIVES", x, fonts)

    cy           = HUD_H // 2 + 2

    for i in range(snake.max_lives):
        hx = x + i * spacing + size * 2

        if i < snake.lives:
            # glow halo
            gs = pygame.Surface((size * 6, size * 6), pygame.SRCALPHA)
            pygame.draw.circle(gs, (*col_glow, 35), (size * 3, size * 3), size * 3)
            surf.blit(gs, (hx - size * 3, cy - size * 3))
            _draw_heart(surf, hx, cy, size, col_full)
        else:
            _draw_heart(surf, hx, cy, size, col_empty, alpha=120)

    # ── Immortality arc + countdown on the first empty heart ──────────────────
    if snake.is_life_immortal():
        slot = snake.lives          # index of the just-lost life
        if slot < snake.max_lives:
            hx    = x + slot * spacing + size * 2
            pct   = snake.life_immortal_pct()
            arc_r = size * 2 + 6
            rect  = pygame.Rect(hx - arc_r, cy - arc_r, arc_r * 2, arc_r * 2)
            flash = (now // 180) % 2 == 0
            arc_col = (0, 230, 255) if flash else (0, 110, 160)
            end_a = math.radians(90 + 360 * pct)
            if end_a > math.radians(92):
                pygame.draw.arc(surf, arc_col, rect, math.radians(90), end_a, 3)

        # Timer seconds remaining — shown right of the hearts
        secs = snake.immortal_seconds_left()
        timer_x = x + snake.max_lives * spacing + 4
        flash2   = (now // 180) % 2 == 0
        t_col    = (0, 230, 255) if flash2 else (0, 110, 160)
        t_surf   = fonts["sm"].render(f"IMMUNE {secs:.1f}s", True, t_col)
        surf.blit(t_surf, (timer_x, cy - t_surf.get_height() // 2))
        return timer_x + t_surf.get_width()

    return x + snake.max_lives * spacing


# ── Ammo pips ─────────────────────────────────────────────────────────────────

def _draw_ammo(surf: pygame.Surface, ammo: int, x: int, fonts: dict) -> int:
    _section_label(surf, "AMMO", x, fonts)
    pip_w, pip_h = 8, 12
    gap          = 3
    cy           = HUD_H // 2 + 2
    show         = min(ammo, 10)
    for i in range(10):
        px  = x + i * (pip_w + gap)
        py  = cy - pip_h // 2
        col = C_AMMO if i < show else (20, 30, 50)
        pygame.draw.rect(surf, col, (px, py, pip_w, pip_h), border_radius=2)
        if i < show:
            pygame.draw.rect(surf, (120, 230, 255), (px, py, pip_w, pip_h), 1, border_radius=2)
    end_x = x + 10 * (pip_w + gap)
    if ammo == 0:
        out_t = fonts["sm"].render("OUT", True, C_RED)
        surf.blit(out_t, (end_x + 2, cy - out_t.get_height() // 2))
        end_x += out_t.get_width() + 4
    elif ammo > 10:
        ov_t = fonts["sm"].render(f"+{ammo - 10}", True, C_AMMO)
        surf.blit(ov_t, (end_x + 2, cy - ov_t.get_height() // 2))
        end_x += ov_t.get_width() + 4
    return end_x


# ── Key diamonds ──────────────────────────────────────────────────────────────

def _draw_keys(surf: pygame.Surface, keys: int, x: int, fonts: dict) -> int:
    _section_label(surf, f"KEYS  {keys}/5", x, fonts)
    cy           = HUD_H // 2 + 2
    ksize = 8
    spacing = 22
    for i in range(5):
        kx = x + i * spacing + ksize
        col = C_KEY if i < keys else (40, 30, 0)
        pts = [(kx, cy - ksize), (kx + ksize, cy),
               (kx, cy + ksize), (kx - ksize, cy)]
        pygame.draw.polygon(surf, col, pts)
        if i < keys:
            pygame.draw.polygon(surf, (255, 255, 160), pts, 1)
    return x + 5 * spacing + ksize


# ── Dash bar ──────────────────────────────────────────────────────────────────

def _draw_dash(surf: pygame.Surface, snake, x: int, fonts: dict) -> int:
    pct   = snake.dash_cooldown_pct()
    ready = pct >= 1.0
    col   = C_SNAKE_I if ready else (40, 60, 100)

    _section_label(surf, "DASH", x, fonts)

    bar_w, bar_h = 88, 16
    cy           = HUD_H // 2 + 2
    by = cy - bar_h // 2

    pygame.draw.rect(surf, (15, 20, 45), (x, by, bar_w, bar_h), border_radius=8)
    if pct > 0:
        pygame.draw.rect(surf, col, (x, by, int(bar_w * pct), bar_h), border_radius=8)
    draw_glowing_rect(surf, C_HUD_BORDER, (x, by, bar_w, bar_h), 1, 2)

    label = "READY" if ready else f"{int(pct * 100)}%"
    lt    = fonts["sm"].render(label, True, C_WHITE)
    surf.blit(lt, (x + bar_w // 2 - lt.get_width() // 2, by + bar_h // 2 - lt.get_height() // 2))

    return x + bar_w


# ═══════════════════════════════════════════════════════════════════════════════
# Public HUD draw
# ═══════════════════════════════════════════════════════════════════════════════

def draw_hud(surf: pygame.Surface, game: dict) -> None:
    fonts = get_fonts()
    snake = game["snake"]

    # ── Background panel ──────────────────────────────────────────────────────
    panel = pygame.Surface((W, HUD_H), pygame.SRCALPHA)
    panel.fill((4, 4, 18, 215))
    surf.blit(panel, (0, 0))
    pygame.draw.line(surf, C_HUD_BORDER, (0, HUD_H), (W, HUD_H), 1)

    # ── Left-to-right sections ────────────────────────────────────────────────
    cursor = 14

    right_lives = _draw_lives(surf, snake, cursor, fonts)
    cursor = right_lives + 14
    _vdivider(surf, cursor - 7)

    right_hp = _draw_hp(surf, snake, cursor, fonts)
    cursor = right_hp + 14
    _vdivider(surf, cursor - 7)

    right_keys = _draw_keys(surf, game["keys"], cursor, fonts)
    cursor = right_keys + 14
    _vdivider(surf, cursor - 7)

    right_dash = _draw_dash(surf, snake, cursor, fonts)
    cursor = right_dash + 14
    _vdivider(surf, cursor - 7)

    _draw_ammo(surf, game["ammo"], cursor, fonts)

    # ── Right-aligned: time / kills / level ───────────────────────────────────
    elapsed = int((pygame.time.get_ticks() - game["start"]) / 1000)
    lvl     = "BOSS" if game.get("boss_level") else f"LV{game['level']}"
    lvl_col = C_BOSS if game.get("boss_level") else C_WHITE
    line    = f"{lvl}  |  T {elapsed:04d}s  |  KILLS {game['kills']}"
    rt      = fonts["mono"].render(line, True, lvl_col)
    surf.blit(rt, (W - rt.get_width() - 14, HUD_H // 2 - rt.get_height() // 2))

    # ── Boss level objective text ────────────────────────────────────────────
    if game.get("boss_level"):
        now_ms = pygame.time.get_ticks()
        if (now_ms // 600) % 2 == 0:
            obj = fonts["mono"].render("★  KILL THE BOSS TO WIN  ★", True, (220, 60, 255))
        else:
            obj = fonts["mono"].render("★  KILL THE BOSS TO WIN  ★", True, (140, 20, 180))
        surf.blit(obj, (W // 2 - obj.get_width() // 2, HUD_H + 6))

    # ── Boss HP bar (bottom centre) ───────────────────────────────────────────
    boss = game.get("boss")
    if boss and not boss.dead:
        from .entities import Boss as BossClass
        bw   = 500
        bx   = W // 2 - bw // 2
        by   = H - 60

        pnl2 = pygame.Surface((bw + 40, 60), pygame.SRCALPHA)
        pnl2.fill((10, 0, 20, 210))
        surf.blit(pnl2, (bx - 20, by - 10))
        pygame.draw.rect(surf, C_BOSS, (bx - 20, by - 10, bw + 40, 60), 1)

        phase     = boss._get_phase()
        phase_col = [C_BOSS, (220, 50, 255), (255, 0, 100)][phase]
        name_t    = fonts["med"].render(
            f"☠ VOID SOVEREIGN — {BossClass.PHASE_NAMES[phase]} ☠", True, phase_col
        )
        surf.blit(name_t, (W // 2 - name_t.get_width() // 2, by - 8))
        draw_health_bar(surf, bx, by + 26, bw, 18, boss.hp, boss.max_hp,
                        phase_col, (40, 0, 40), f"{boss.hp}/{boss.max_hp}")
        # Phase divider lines at HP 80 and 40 — cyan glow, no number
        for div_hp in [80, 40]:
            div_x = bx + int(bw * div_hp / boss.max_hp)
            # Glow layers
            for gw in range(5, 0, -1):
                ga = int(60 * (gw / 5))
                gs = pygame.Surface((gw * 2 + 2, 24), pygame.SRCALPHA)
                pygame.draw.line(gs, (0, 200, 255, ga),
                                 (gw, 0), (gw, 23), gw * 2)
                surf.blit(gs, (div_x - gw, by + 24))
            # Solid cyan line
            pygame.draw.line(surf, (0, 220, 255),
                             (div_x, by + 24), (div_x, by + 46), 2)
        if boss.shield > 0:
            sw = int(bw * boss.shield / boss.shield_max)
            pygame.draw.rect(surf, C_AMMO, (bx, by + 26, sw, 18), 2, border_radius=4)
            surf.blit(fonts["sm"].render("SHIELD", True, C_AMMO),
                      (bx + bw // 2 - 20, by + 28))


# ═══════════════════════════════════════════════════════════════════════════════
# Screens
# ═══════════════════════════════════════════════════════════════════════════════

# ── Menu button rects (mutated each draw, read by main.py for clicks) ────────
START_BTN     = pygame.Rect(0, 0, 320, 56)
TUTORIAL_BTN  = pygame.Rect(0, 0, 320, 56)
ANALYTICS_BTN = pygame.Rect(0, 0, 320, 56)
QUIT_BTN      = pygame.Rect(0, 0, 320, 56)


def _draw_menu_button(surf, rect, label, base_col, hover, fonts, enabled=True):
    fill_col = (0, 0, 0) if not enabled else (
        (base_col[0]//4 + 30, base_col[1]//4 + 30, base_col[2]//4 + 30)
        if hover else (8, 12, 22))
    border_col = base_col if enabled else (40, 40, 50)
    text_col   = base_col if enabled else (60, 60, 70)
    pygame.draw.rect(surf, fill_col, rect, border_radius=10)
    pygame.draw.rect(surf, border_col, rect, 2, border_radius=10)
    if hover and enabled:
        # Glow
        for w in range(8, 0, -2):
            gs = pygame.Surface((rect.w + w * 2, rect.h + w * 2), pygame.SRCALPHA)
            pygame.draw.rect(gs, (*base_col, 30),
                             (0, 0, rect.w + w * 2, rect.h + w * 2),
                             2, border_radius=10 + w)
            surf.blit(gs, (rect.x - w, rect.y - w))
    bt = fonts["med"].render(label, True, text_col)
    surf.blit(bt, (rect.centerx - bt.get_width() // 2,
                   rect.centery - bt.get_height() // 2))


def draw_menu(surf: pygame.Surface,
              has_data: bool = False,
              start_hover: bool = False,
              tutorial_hover: bool = False,
              analytics_hover: bool = False,
              quit_hover: bool = False) -> None:
    fonts = get_fonts()
    surf.fill(C_BG)
    t = pygame.time.get_ticks() / 1000

    # Animated grid
    for x in range(0, W, 60):
        a = int(30 + 20 * math.sin(t + x * 0.01))
        pygame.draw.line(surf, (0, a, a), (x, 0), (x, H))
    for y in range(0, H, 60):
        a = int(30 + 20 * math.sin(t + y * 0.01))
        pygame.draw.line(surf, (0, a, a), (0, y), (W, y))

    # Title
    pulse = 1.0 + 0.04 * math.sin(t * 3)
    tfnt  = pygame.font.SysFont("consolas", int(90 * pulse), bold=True)
    t1    = tfnt.render("NEON SERPENT", True, C_SNAKE_H)
    for off in [(3, 3), (-3, -3), (3, -3), (-3, 3)]:
        g = tfnt.render("NEON SERPENT", True, (0, 60, 30))
        surf.blit(g, (W // 2 - g.get_width() // 2 + off[0], 150 + off[1]))
    surf.blit(t1, (W // 2 - t1.get_width() // 2, 150))

    sub = fonts["med"].render("MAZE RUNNER · BOSS SLAYER", True, C_AMMO)
    surf.blit(sub, (W // 2 - sub.get_width() // 2, 260))

    # Buttons
    btn_w  = 320
    btn_h  = 56
    btn_x  = W // 2 - btn_w // 2
    base_y = 360
    spacing = 16

    START_BTN.update    (btn_x, base_y + 0 * (btn_h + spacing), btn_w, btn_h)
    TUTORIAL_BTN.update (btn_x, base_y + 1 * (btn_h + spacing), btn_w, btn_h)
    ANALYTICS_BTN.update(btn_x, base_y + 2 * (btn_h + spacing), btn_w, btn_h)
    QUIT_BTN.update     (btn_x, base_y + 3 * (btn_h + spacing), btn_w, btn_h)

    _draw_menu_button(surf, START_BTN,    "START GAME",     (80, 255, 120),
                      start_hover, fonts)
    _draw_menu_button(surf, TUTORIAL_BTN, "TUTORIAL",       (0, 200, 255),
                      tutorial_hover, fonts)
    _draw_menu_button(surf, ANALYTICS_BTN,
                      "DATA ANALYTICS" if has_data else "DATA ANALYTICS  (play first)",
                      (200, 80, 255),
                      analytics_hover, fonts, enabled=has_data)
    _draw_menu_button(surf, QUIT_BTN,     "QUIT GAME",      (255, 80, 100),
                      quit_hover, fonts)


# ═══════════════════════════════════════════════════════════════════════════════
# Tutorial Screen
# ═══════════════════════════════════════════════════════════════════════════════

TUTORIAL_BACK_BTN = pygame.Rect(W // 2 - 120, H - 80, 240, 48)


def draw_tutorial(surf: pygame.Surface, back_hover: bool = False) -> None:
    fonts = get_fonts()
    surf.fill(C_BG)

    title = pygame.font.SysFont("consolas", 56, bold=True).render(
        "TUTORIAL", True, C_HUD_BORDER)
    surf.blit(title, (W // 2 - title.get_width() // 2, 40))

    sections = [
        ("CONTROLS", [
            ("Mouse",       "move snake (head follows cursor)"),
            ("Left Click",  "shoot — auto-locks onto nearest enemy"),
            ("Right Click", "DASH — teleport, 2s invincible + phase walls"),
            ("ESC",         "pause game"),
        ]),
        ("COMBAT", [
            ("HP",      "3 hits per life, then you lose 1 life"),
            ("Lives",   "10 lives total — game over at 0"),
            ("Immune",  "5 seconds invincible after losing a life"),
            ("Missile", "auto-fires at boss on pickup, deals 8 damage"),
        ]),
        ("OBJECTIVE", [
            ("Levels 1-2", "collect 5 keys to unlock the EXIT"),
            ("Level 3",    "no exit — kill the VOID SOVEREIGN to win"),
            ("Boss",       "3 phases at HP 80 / 40, each grants new items"),
        ]),
    ]

    base_y = 130
    for sec_title, items in sections:
        st = fonts["med"].render(sec_title, True, C_GOLD)
        surf.blit(st, (W // 2 - 380, base_y))
        base_y += 38
        for key, desc in items:
            kt = fonts["sm"].render(key, True, (0, 200, 255))
            dt = fonts["sm"].render(f"->  {desc}", True, C_DIM)
            surf.blit(kt, (W // 2 - 360, base_y))
            surf.blit(dt, (W // 2 - 220, base_y))
            base_y += 22
        base_y += 14

    # Back button
    col = (0, 200, 255) if back_hover else (50, 80, 120)
    pygame.draw.rect(surf, (10, 14, 28), TUTORIAL_BACK_BTN, border_radius=8)
    pygame.draw.rect(surf, col, TUTORIAL_BACK_BTN, 2, border_radius=8)
    bt = fonts["med"].render("[ BACK ]", True, col)
    surf.blit(bt, (TUTORIAL_BACK_BTN.centerx - bt.get_width() // 2,
                   TUTORIAL_BACK_BTN.centery - bt.get_height() // 2))


# ═══════════════════════════════════════════════════════════════════════════════
# Pause Screen
# ═══════════════════════════════════════════════════════════════════════════════

PAUSE_RESUME_BTN   = pygame.Rect(0, 0, 320, 50)
PAUSE_TUTORIAL_BTN = pygame.Rect(0, 0, 320, 50)
PAUSE_MENU_BTN     = pygame.Rect(0, 0, 320, 50)
PAUSE_QUIT_BTN     = pygame.Rect(0, 0, 320, 50)


def draw_pause(surf: pygame.Surface,
               resume_hover: bool = False,
               tutorial_hover: bool = False,
               menu_hover: bool = False,
               quit_hover: bool = False) -> None:
    fonts = get_fonts()

    # Dark overlay over the game
    ov = pygame.Surface((W, H), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 200))
    surf.blit(ov, (0, 0))

    # Title
    title = pygame.font.SysFont("consolas", 84, bold=True).render(
        "PAUSED", True, C_WHITE)
    surf.blit(title, (W // 2 - title.get_width() // 2, 100))

    # Buttons
    btn_w = 320
    btn_h = 50
    bx    = W // 2 - btn_w // 2
    by    = 240
    sp    = 14

    PAUSE_RESUME_BTN.update  (bx, by + 0 * (btn_h + sp), btn_w, btn_h)
    PAUSE_TUTORIAL_BTN.update(bx, by + 1 * (btn_h + sp), btn_w, btn_h)
    PAUSE_MENU_BTN.update    (bx, by + 2 * (btn_h + sp), btn_w, btn_h)
    PAUSE_QUIT_BTN.update    (bx, by + 3 * (btn_h + sp), btn_w, btn_h)

    _draw_menu_button(surf, PAUSE_RESUME_BTN,   "RESUME",        (80, 255, 120),
                      resume_hover, fonts)
    _draw_menu_button(surf, PAUSE_TUTORIAL_BTN, "TUTORIAL",      (0, 200, 255),
                      tutorial_hover, fonts)
    _draw_menu_button(surf, PAUSE_MENU_BTN,     "QUIT TO MENU",  (255, 180, 0),
                      menu_hover, fonts)
    _draw_menu_button(surf, PAUSE_QUIT_BTN,     "QUIT GAME",     (255, 80, 100),
                      quit_hover, fonts)

    # Warning text
    warn = fonts["sm"].render(
        "⚠  Quitting will discard this session's stats — they will not be saved.",
        True, (255, 200, 80))
    surf.blit(warn, (W // 2 - warn.get_width() // 2, by + 4 * (btn_h + sp) + 12))


def draw_death(surf: pygame.Surface, cause: str = "") -> None:
    fonts   = get_fonts()
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((80, 0, 0, 160))
    surf.blit(overlay, (0, 0))
    t1 = fonts["big"].render("YOU DIED", True, C_RED)
    surf.blit(t1, (W // 2 - t1.get_width() // 2, H // 2 - 80))
    if cause:
        t2 = fonts["med"].render(cause, True, (200, 100, 100))
        surf.blit(t2, (W // 2 - t2.get_width() // 2, H // 2 + 20))
    t3 = fonts["mono"].render("returning to menu...", True, C_DIM)
    surf.blit(t3, (W // 2 - t3.get_width() // 2, H // 2 + 80))


def draw_win(surf: pygame.Surface) -> None:
    fonts   = get_fonts()
    t       = pygame.time.get_ticks() / 1000
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 30, 0, 160))
    surf.blit(overlay, (0, 0))
    pulse = 1 + 0.05 * math.sin(t * 4)
    fnt   = pygame.font.SysFont("consolas", int(80 * pulse), bold=True)
    t1    = fnt.render("VICTORY!", True, C_GOLD)
    surf.blit(t1, (W // 2 - t1.get_width() // 2, H // 2 - 80))
    t2 = fonts["med"].render("THE VOID SOVEREIGN IS VANQUISHED", True, C_EXIT)
    surf.blit(t2, (W // 2 - t2.get_width() // 2, H // 2 + 20))
    t3 = fonts["mono"].render("press ENTER to play again", True, C_WHITE)
    surf.blit(t3, (W // 2 - t3.get_width() // 2, H // 2 + 90))


def draw_boss_intro(surf: pygame.Surface, alpha: int) -> None:
    fonts = get_fonts()
    s     = pygame.Surface((W, H), pygame.SRCALPHA)
    s.fill((20, 0, 30, min(200, alpha)))
    surf.blit(s, (0, 0))
    if alpha > 100:
        t1 = fonts["big"].render("BOSS INCOMING", True, (*C_BOSS, min(255, alpha)))
        ts = pygame.Surface(t1.get_size(), pygame.SRCALPHA)
        ts.blit(t1, (0, 0))
        surf.blit(ts, (W // 2 - t1.get_width() // 2, H // 2 - 60))
        t2 = fonts["med"].render("VOID SOVEREIGN", True, (*C_BOSS, min(220, alpha - 40)))
        surf.blit(t2, (W // 2 - t2.get_width() // 2, H // 2 + 40))


# ═══════════════════════════════════════════════════════════════════════════════
# Level Transition Screen
# ═══════════════════════════════════════════════════════════════════════════════

def _draw_skull(surf: pygame.Surface, cx: int, cy: int, r: int,
                color: tuple, alpha: int = 255) -> None:
    """
    Draw a simple skull shape centred at (cx, cy) with radius r.
    Built from: cranium circle + two eye holes + teeth row.
    """
    s = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
    ox, oy = r * 2, r * 2   # local centre

    # Cranium
    pygame.draw.circle(s, (*color, alpha), (ox, oy - r // 6), int(r * 0.85))

    # Jaw (rectangle below cranium)
    jaw_w = int(r * 1.1)
    jaw_h = int(r * 0.5)
    jaw_x = ox - jaw_w // 2
    jaw_y = oy - r // 6 + int(r * 0.55)
    pygame.draw.rect(s, (*color, alpha), (jaw_x, jaw_y, jaw_w, jaw_h),
                     border_radius=int(r * 0.15))

    # Eyes (black holes)
    eye_r   = max(2, r // 4)
    eye_off = r // 3
    pygame.draw.circle(s, (0, 0, 0, 255), (ox - eye_off, oy - r // 4), eye_r)
    pygame.draw.circle(s, (0, 0, 0, 255), (ox + eye_off, oy - r // 4), eye_r)

    # Nose hole (small triangle-ish)
    nose_r = max(1, r // 6)
    pygame.draw.circle(s, (0, 0, 0, 255), (ox, oy + r // 8), nose_r)

    # Teeth (3 small rects along bottom of jaw)
    tooth_w = max(2, jaw_w // 5)
    tooth_h = max(2, jaw_h // 2)
    for i in range(3):
        tx = jaw_x + jaw_w // 5 + i * (jaw_w // 3) - tooth_w // 2
        ty = jaw_y + jaw_h - tooth_h
        pygame.draw.rect(s, (0, 0, 0, 255), (tx, ty, tooth_w, tooth_h))

    surf.blit(s, (cx - r * 2, cy - r * 2))


def draw_level_transition(surf: pygame.Surface,
                           entering_level: int,
                           cleared_levels: list[int],
                           snake=None,
                           current_ammo: int = 0,
                           elapsed_ms: int = 0,
                           duration_ms: int = 4000) -> None:
    """
    Full-screen level transition shown for 4 s before each level.

    Parameters
    ----------
    entering_level : 1, 2, or 3  (3 = boss)
    cleared_levels : list of level numbers already completed, e.g. [1, 2]
    snake          : Snake object for HP/Lives display (None on first entry)
    elapsed_ms     : ms since transition started (drives animations)
    duration_ms    : total display time in ms
    """
    fonts = get_fonts()
    now   = elapsed_ms

    # ── Dark background ───────────────────────────────────────────────────────
    surf.fill((5, 3, 12))

    # Subtle animated grid
    t = pygame.time.get_ticks() / 1000
    for gx in range(0, W, 80):
        a = int(15 + 8 * math.sin(t * 0.7 + gx * 0.01))
        pygame.draw.line(surf, (0, a, a), (gx, 0), (gx, H))
    for gy in range(0, H, 80):
        a = int(15 + 8 * math.sin(t * 0.7 + gy * 0.01))
        pygame.draw.line(surf, (0, a, a), (0, gy), (W, gy))

    # ── Main text ─────────────────────────────────────────────────────────────
    if entering_level == 3:
        main_text = "ENTERING BOSS STAGE"
        txt_color = C_BOSS
    else:
        main_text = f"ENTERING LEVEL {entering_level}"
        txt_color = C_WHITE

    # Fade in during first 500 ms
    fade_alpha = min(255, int(255 * elapsed_ms / 500))
    pulse      = 1.0 + 0.03 * math.sin(t * 3)
    big_fnt    = pygame.font.SysFont("consolas", int(64 * pulse), bold=True)
    txt_surf   = big_fnt.render(main_text, True, txt_color)
    txt_surf.set_alpha(fade_alpha)

    # Glow copies
    for off in [(3, 3), (-3, -3), (3, -3), (-3, 3)]:
        glow = big_fnt.render(main_text, True,
                              (txt_color[0] // 4, txt_color[1] // 4, txt_color[2] // 4))
        glow.set_alpha(fade_alpha // 2)
        surf.blit(glow, (W // 2 - txt_surf.get_width() // 2 + off[0],
                         H // 2 - 120 + off[1]))
    surf.blit(txt_surf, (W // 2 - txt_surf.get_width() // 2, H // 2 - 120))

    # ── Stage indicators (3 nodes) ────────────────────────────────────────────
    node_r   = 32
    spacing  = 160
    total_w  = spacing * 2 + node_r * 2
    start_x  = W // 2 - total_w // 2 + node_r
    node_y   = H // 2 + 20

    # Connecting lines between nodes
    for i in range(2):
        lx1 = start_x + i * spacing + node_r
        lx2 = start_x + (i + 1) * spacing - node_r
        ly  = node_y
        pygame.draw.line(surf, (40, 40, 60), (lx1, ly), (lx2, ly), 3)

    for i in range(3):      # i=0 → level1, i=1 → level2, i=2 → boss
        level_num = i + 1
        cx = start_x + i * spacing
        cy = node_y
        is_boss    = (level_num == 3)
        is_cleared = level_num in cleared_levels
        is_current = (level_num == entering_level)

        # Determine colour
        if is_cleared:
            col   = (30, 200, 80)     # green
            alpha = 255
        elif is_current:
            # Pulsing white (or purple for boss)
            blink = int(200 + 55 * math.sin(t * 4))
            col   = (blink, blink, blink) if not is_boss else (blink, 0, blink)
            alpha = 255
        else:
            col   = (30, 30, 40)      # dark unvisited
            alpha = 200

        if is_boss:
            # ── Skull (node 3) ─────────────────────────────────────────────
            _draw_skull(surf, cx, cy, node_r, col, alpha)
            # Outline ring
            ring_col = (30, 200, 80) if is_cleared else \
                       ((180, 0, 255) if is_current else (40, 40, 55))
            pygame.draw.circle(surf, ring_col, (cx, cy), node_r + 4, 2)
        else:
            # ── Circle (nodes 1 & 2) ───────────────────────────────────────
            pygame.draw.circle(surf, col, (cx, cy), node_r)
            ring_col = (30, 200, 80) if is_cleared else \
                       (C_HUD_BORDER if is_current else (40, 40, 55))
            pygame.draw.circle(surf, ring_col, (cx, cy), node_r + 3, 2)

            # Checkmark if cleared
            if is_cleared:
                ck_pts = [
                    (cx - node_r // 3, cy),
                    (cx - node_r // 8, cy + node_r // 3),
                    (cx + node_r // 2, cy - node_r // 3),
                ]
                pygame.draw.lines(surf, (255, 255, 255), False, ck_pts, 3)
            elif is_current:
                # Level number inside circle
                num_t = fonts["med"].render(str(level_num), True, C_WHITE)
                surf.blit(num_t, (cx - num_t.get_width() // 2,
                                  cy - num_t.get_height() // 2))

        # Label below node
        if is_boss:
            lbl = "BOSS"
        else:
            lbl = f"LEVEL {level_num}"
        lbl_col = (30, 200, 80) if is_cleared else \
                  (C_WHITE if is_current else (60, 60, 80))
        lbl_t = fonts["sm"].render(lbl, True, lbl_col)
        surf.blit(lbl_t, (cx - lbl_t.get_width() // 2, cy + node_r + 10))

    # ── HP / Lives carried over (skip on level 1 first entry) ────────────────
    if snake is not None and entering_level > 1:
        ammo_col  = (255, 60, 60) if current_ammo == 0 else (0, 200, 255)
        ammo_text = "AMMO  OUT" if current_ammo == 0 else f"AMMO  {current_ammo}"
        items_info = [
            (f"LIVES  {snake.lives}/{snake.max_lives}", (255, 80, 100)),
            (f"HP  {snake.hp}/{snake.MAX_HP}",          (80, 230, 100)),
            (ammo_text,                                  ammo_col),
        ]
        total_w = sum(fonts["mono"].size(t)[0] for t, _ in items_info) + 80
        sx = W // 2 - total_w // 2
        sy = H // 2 + 118
        for txt, col in items_info:
            ts = fonts["mono"].render(txt, True, col)
            ts.set_alpha(fade_alpha)
            surf.blit(ts, (sx, sy))
            sx += ts.get_width() + 40

    # ── "Get ready" blinking hint ─────────────────────────────────────────────
    remaining = max(0, duration_ms - elapsed_ms)
    if remaining < 2000 and (pygame.time.get_ticks() // 400) % 2 == 0:
        ready_t = fonts["mono"].render("GET READY...", True, C_DIM)
        surf.blit(ready_t, (W // 2 - ready_t.get_width() // 2, H // 2 + 160))


# ═══════════════════════════════════════════════════════════════════════════════
# Boss Phase Transition Animation
# ═══════════════════════════════════════════════════════════════════════════════

PHASE_ANIM_DURATION = 2000   # ms total

# Phase colours
_PHASE_COLS = [
    (200,   0, 255),   # phase 0 → 1 : purple
    (255,  20,  20),   # phase 1 → 2 : blood red
]


def draw_phase_transition(
    surf: pygame.Surface,
    boss_pos: tuple,
    entering_phase: int,
    elapsed_ms: int,
) -> None:
    """
    Full-screen boss phase-change animation.

    Timeline (2 s total)
    --------------------
    0–300 ms   Shockwave + white flash
    300–800 ms Boss pulse rays
    800–1500ms Phase name text reveal + flicker
    1500–2000ms Fade out
    """
    now    = elapsed_ms
    total  = PHASE_ANIM_DURATION
    fonts  = get_fonts()
    t_sec  = now / 1000
    col    = _PHASE_COLS[min(entering_phase - 1, len(_PHASE_COLS) - 1)]
    name   = ["AWAKENING", "ENRAGED", "FINAL FORM"][entering_phase]
    bx, by = boss_pos

    # ── Shockwave + Flash (0–300 ms) ─────────────────────────────────────────
    if now < 300:
        # White flash fades
        flash_a = int(220 * (1 - now / 300))
        fl = pygame.Surface((W, H), pygame.SRCALPHA)
        fl.fill((255, 255, 255, flash_a))
        surf.blit(fl, (0, 0))

        # Expanding shockwave rings
        for ring in range(3):
            delay  = ring * 80
            if now < delay:
                continue
            prog   = (now - delay) / 300
            radius = int(prog * max(W, H) * 0.8)
            alpha  = int(180 * (1 - prog))
            if radius > 0 and alpha > 0:
                rs = pygame.Surface((W, H), pygame.SRCALPHA)
                pygame.draw.circle(rs, (*col, alpha), (bx, by), radius, 4)
                surf.blit(rs, (0, 0))

    # ── Dark overlay for rest of animation ───────────────────────────────────
    if now >= 200:
        fade_in  = min(1.0, (now - 200) / 200)
        fade_out = 1.0 if now < 1500 else max(0.0, 1 - (now - 1500) / 500)
        ov_alpha = int(180 * fade_in * fade_out)
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, ov_alpha))
        surf.blit(ov, (0, 0))

    # ── Boss pulse + energy rays (300–800 ms) ─────────────────────────────────
    if 300 <= now < 900:
        prog  = (now - 300) / 600
        # Pulsing glow rings around boss
        for ring in range(5):
            pulse = math.sin(prog * math.pi * 2 - ring * 0.4)
            r     = int(30 + ring * 18 + pulse * 12)
            alpha = max(0, int(160 * (1 - ring / 5) * math.sin(prog * math.pi)))
            if r > 0 and alpha > 0:
                gs = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(gs, (*col, alpha), (r + 2, r + 2), r, 3)
                surf.blit(gs, (bx - r - 2, by - r - 2))
        # Energy rays 8 directions
        ray_alpha = int(200 * math.sin(prog * math.pi))
        ray_len   = int(60 + prog * 200)
        if ray_alpha > 0:
            rs = pygame.Surface((W, H), pygame.SRCALPHA)
            for i in range(8):
                angle = math.radians(i * 45 + prog * 180)
                ex    = bx + int(math.cos(angle) * ray_len)
                ey    = by + int(math.sin(angle) * ray_len)
                pygame.draw.line(rs, (*col, ray_alpha), (bx, by), (ex, ey), 3)
            surf.blit(rs, (0, 0))

    # ── Phase name text (800–1800 ms) ─────────────────────────────────────────
    if 700 <= now < 1800:
        prog     = (now - 700) / 300     # 0→1 slide in
        slide_y  = int(H // 2 - 40 + (1 - min(1.0, prog)) * 60)

        # Flicker: rapid blink 800-1000ms, then steady 1000-1600ms, fade 1600-1800ms
        if now < 1000:
            visible = (now // 80) % 2 == 0
        elif now < 1600:
            visible = True
        else:
            visible = (now // 120) % 2 == 0

        if visible:
            # Glow copies
            big_fnt = pygame.font.SysFont("consolas", 68, bold=True)
            label   = f"— {name} —"
            for off in [(4,4),(-4,-4),(4,-4),(-4,4),(0,6),(0,-6),(6,0),(-6,0)]:
                glow = big_fnt.render(label, True,
                                      (col[0]//3, col[1]//3, col[2]//3))
                glow.set_alpha(120)
                surf.blit(glow, (W//2 - glow.get_width()//2 + off[0],
                                 slide_y + off[1]))
            # Main text
            txt = big_fnt.render(label, True, col)
            surf.blit(txt, (W//2 - txt.get_width()//2, slide_y))

            # Sub label
            sub_labels = ["", "PHASE 2 BEGINS", "FINAL PHASE"]
            if entering_phase > 0:
                sub = fonts["med"].render(sub_labels[entering_phase], True, C_WHITE)
                sub.set_alpha(int(200 * min(1.0, (now - 900) / 200)))
                surf.blit(sub, (W//2 - sub.get_width()//2, slide_y + 78))

    # ── Particle sparks around screen edges ──────────────────────────────────
    if 300 <= now < 1600:
        prog = (now - 300) / 1300
        # Static decorative corner lines
        corner_alpha = int(160 * math.sin(prog * math.pi))
        if corner_alpha > 0:
            cs = pygame.Surface((W, H), pygame.SRCALPHA)
            length = int(80 + prog * 60)
            for cx2, cy2, dx, dy in [(0,0,1,1),(W,0,-1,1),(0,H,1,-1),(W,H,-1,-1)]:
                pygame.draw.line(cs, (*col, corner_alpha),
                                 (cx2, cy2),
                                 (cx2 + dx*length, cy2), 3)
                pygame.draw.line(cs, (*col, corner_alpha),
                                 (cx2, cy2),
                                 (cx2, cy2 + dy*length), 3)
            surf.blit(cs, (0, 0))
