"""
renderer.py
Stateless drawing helpers shared across the whole game.
All functions accept a pygame.Surface target so they are testable
without a display.
"""
import pygame
from .constants import C_HUD_BORDER, C_WHITE, get_fonts


def lerp_color(a: tuple, b: tuple, t: float) -> tuple:
    """Linear interpolation between two RGB tuples."""
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def draw_glowing_circle(
    surf: pygame.Surface,
    color: tuple,
    pos: tuple,
    r: int,
    glow: int = 8,
) -> None:
    for i in range(glow, 0, -1):
        alpha = int(80 * (i / glow))
        size  = r * 2 + glow * 4
        s     = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(s, (*color, alpha), (r + glow * 2, r + glow * 2), r + i)
        surf.blit(s, (pos[0] - r - glow * 2, pos[1] - r - glow * 2))
    pygame.draw.circle(surf, color, pos, r)


def draw_glowing_rect(
    surf: pygame.Surface,
    color: tuple,
    rect: tuple,
    width: int = 2,
    glow: int = 6,
) -> None:
    for i in range(glow, 0, -1):
        alpha = int(80 * (i / glow))
        s     = pygame.Surface((rect[2] + glow * 4, rect[3] + glow * 4), pygame.SRCALPHA)
        pygame.draw.rect(
            s, (*color, alpha),
            (glow * 2 - i, glow * 2 - i, rect[2] + i * 2, rect[3] + i * 2),
            width,
        )
        surf.blit(s, (rect[0] - glow * 2, rect[1] - glow * 2))
    pygame.draw.rect(surf, color, rect, width)


def draw_health_bar(
    surf: pygame.Surface,
    x: int, y: int, w: int, h: int,
    val: float, maxval: float,
    col_full: tuple,
    col_empty: tuple = (30, 30, 30),
    label: str = "",
) -> None:
    pygame.draw.rect(surf, col_empty, (x, y, w, h), border_radius=4)
    fill = int(w * max(0, val / maxval))
    if fill > 0:
        pygame.draw.rect(surf, col_full, (x, y, fill, h), border_radius=4)
    draw_glowing_rect(surf, C_HUD_BORDER, (x, y, w, h), 1, 3)
    if label:
        fonts = get_fonts()
        t = fonts["sm"].render(label, True, C_WHITE)
        surf.blit(t, (x + w // 2 - t.get_width() // 2, y + h // 2 - t.get_height() // 2))
