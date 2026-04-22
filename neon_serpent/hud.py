"""
hud.py
All overlay / screen-rendering functions: HUD, menus, death, win, intro.
None of these functions own state – they receive what they need as arguments.
"""
import math
import pygame
from .constants import (
    W, H,
    C_BG, C_SNAKE_H, C_SNAKE_I, C_AMMO, C_KEY, C_EXIT,
    C_HUD_BORDER, C_BOSS, C_BOSS_PROJ,
    C_RED, C_GOLD, C_WHITE, C_DIM,
    get_fonts,
)
from .renderer  import draw_glowing_rect, draw_health_bar


# ── HUD (in-game overlay) ─────────────────────────────────────────────────────

def draw_hud(surf: pygame.Surface, game: dict) -> None:
    fonts = get_fonts()
    snake = game["snake"]
    hud_h = 56

    panel = pygame.Surface((W, hud_h), pygame.SRCALPHA)
    panel.fill((5, 5, 20, 200))
    surf.blit(panel, (0, 0))
    pygame.draw.line(surf, C_HUD_BORDER, (0, hud_h), (W, hud_h), 1)

    # HP bar
    draw_health_bar(surf, 12, 14, 160, 22, snake.hp, snake.max_hp,
                    (0, 230, 100), (30, 10, 10), f"HP {snake.hp}/{snake.max_hp}")

    # Ammo pips
    ammo_x = 190
    surf.blit(fonts["mono"].render("AMMO", True, C_DIM), (ammo_x, 10))
    for i in range(10):
        col = C_AMMO if i < game["ammo"] else (30, 30, 60)
        pygame.draw.rect(surf, col, (ammo_x + i * 14, 30, 10, 14), border_radius=2)

    # Keys
    key_x = 350
    surf.blit(fonts["mono"].render(f"KEYS {game['keys']}/5", True, C_KEY), (key_x, 10))
    for i in range(5):
        col = C_KEY if i < game["keys"] else (40, 30, 0)
        pygame.draw.polygon(surf, col, [
            (key_x + i * 22 + 5,  32),
            (key_x + i * 22 + 11, 38),
            (key_x + i * 22 + 5,  44),
            (key_x + i * 22 - 1,  38),
        ])

    # Dash cooldown bar
    dash_x = 520
    pct     = snake.dash_cooldown_pct()
    col_d   = C_SNAKE_I if pct >= 1.0 else (40, 60, 100)
    surf.blit(fonts["mono"].render("DASH", True, C_DIM), (dash_x, 10))
    pygame.draw.rect(surf, (20, 20, 50), (dash_x, 30, 80, 16), border_radius=8)
    if pct > 0:
        pygame.draw.rect(surf, col_d, (dash_x, 30, int(80 * pct), 16), border_radius=8)
    draw_glowing_rect(surf, C_HUD_BORDER, (dash_x, 30, 80, 16), 1, 2)
    if pct >= 1.0:
        surf.blit(fonts["sm"].render("READY", True, C_SNAKE_I), (dash_x + 12, 32))

    # Score / time
    elapsed = int((pygame.time.get_ticks() - game["start"]) / 1000)
    score_t = fonts["mono"].render(
        f"T {elapsed:04d}s  KILLS {game['kills']}", True, C_WHITE
    )
    surf.blit(score_t, (W - score_t.get_width() - 12, 10))

    # Level label
    lvl     = "BOSS LEVEL" if game.get("boss_level") else f"LEVEL {game['level']}"
    lvl_col = C_BOSS if game.get("boss_level") else C_WHITE
    lvl_t   = fonts["mono"].render(lvl, True, lvl_col)
    surf.blit(lvl_t, (W - lvl_t.get_width() - 12, 32))

    # Boss HP bar
    boss = game.get("boss")
    if boss and not boss.dead:
        from .entities import Boss as BossClass
        bw   = 500
        bx   = W // 2 - bw // 2
        by   = H - 70
        pnl  = pygame.Surface((bw + 40, 60), pygame.SRCALPHA)
        pnl.fill((10, 0, 20, 200))
        surf.blit(pnl, (bx - 20, by - 10))
        pygame.draw.rect(surf, C_BOSS, (bx - 20, by - 10, bw + 40, 60), 1)

        phase     = boss._get_phase()
        phase_col = [C_BOSS, (220, 50, 255), (255, 0, 100)][phase]
        name_t    = fonts["med"].render(
            f"☠ VOID SOVEREIGN — {BossClass.PHASE_NAMES[phase]} ☠", True, phase_col
        )
        surf.blit(name_t, (W // 2 - name_t.get_width() // 2, by - 8))
        draw_health_bar(surf, bx, by + 26, bw, 18, boss.hp, boss.max_hp,
                        phase_col, (40, 0, 40), f"{boss.hp}/{boss.max_hp}")
        if boss.shield > 0:
            sw = int(bw * boss.shield / boss.shield_max)
            pygame.draw.rect(surf, C_AMMO, (bx, by + 26, sw, 18), 2, border_radius=4)
            surf.blit(fonts["sm"].render("SHIELD", True, C_AMMO), (bx + bw // 2 - 20, by + 28))


# ── Main Menu ─────────────────────────────────────────────────────────────────

def draw_menu(surf: pygame.Surface) -> None:
    fonts = get_fonts()
    surf.fill(C_BG)
    t = pygame.time.get_ticks() / 1000

    # Animated grid lines
    for x in range(0, W, 60):
        alpha = int(30 + 20 * math.sin(t + x * 0.01))
        pygame.draw.line(surf, (0, alpha, alpha), (x, 0), (x, H))
    for y in range(0, H, 60):
        alpha = int(30 + 20 * math.sin(t + y * 0.01))
        pygame.draw.line(surf, (0, alpha, alpha), (0, y), (W, y))

    # Pulsing title
    pulse = 1.0 + 0.04 * math.sin(t * 3)
    title_fnt = pygame.font.SysFont("consolas", int(90 * pulse), bold=True)
    t1 = title_fnt.render("NEON SERPENT", True, C_SNAKE_H)
    for off in [(3, 3), (-3, -3), (3, -3), (-3, 3)]:
        glow = title_fnt.render("NEON SERPENT", True, (0, 60, 30))
        surf.blit(glow, (W // 2 - glow.get_width() // 2 + off[0], 200 + off[1]))
    surf.blit(t1, (W // 2 - t1.get_width() // 2, 200))

    sub = fonts["med"].render("MAZE RUNNER · BOSS SLAYER", True, C_AMMO)
    surf.blit(sub, (W // 2 - sub.get_width() // 2, 310))

    if int(t * 2) % 2 == 0:
        enter = fonts["med"].render("[ PRESS ENTER TO START ]", True, C_WHITE)
        surf.blit(enter, (W // 2 - enter.get_width() // 2, 420))

    tips = [
        "MOUSE  →  move snake",
        "LEFT CLICK  →  shoot (costs ammo)",
        "RIGHT CLICK  →  DASH (5s cooldown, phase+invincible)",
        "Collect 5 KEYS to open EXIT",
        "LEVEL 3 awaits the VOID SOVEREIGN boss",
    ]
    for i, tip in enumerate(tips):
        col   = C_DIM if i < 4 else C_BOSS
        t_surf = fonts["sm"].render(tip, True, col)
        surf.blit(t_surf, (W // 2 - t_surf.get_width() // 2, 520 + i * 26))


# ── Death Screen ──────────────────────────────────────────────────────────────

def draw_death(surf: pygame.Surface, cause: str = "") -> None:
    fonts = get_fonts()
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


# ── Victory Screen ────────────────────────────────────────────────────────────

def draw_win(surf: pygame.Surface) -> None:
    fonts = get_fonts()
    t = pygame.time.get_ticks() / 1000
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 30, 0, 160))
    surf.blit(overlay, (0, 0))
    pulse   = 1 + 0.05 * math.sin(t * 4)
    fnt     = pygame.font.SysFont("consolas", int(80 * pulse), bold=True)
    t1      = fnt.render("VICTORY!", True, C_GOLD)
    surf.blit(t1, (W // 2 - t1.get_width() // 2, H // 2 - 80))
    t2 = fonts["med"].render("THE VOID SOVEREIGN IS VANQUISHED", True, C_EXIT)
    surf.blit(t2, (W // 2 - t2.get_width() // 2, H // 2 + 20))
    t3 = fonts["mono"].render("press ENTER to play again", True, C_WHITE)
    surf.blit(t3, (W // 2 - t3.get_width() // 2, H // 2 + 90))


# ── Boss Intro Overlay ────────────────────────────────────────────────────────

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
