"""
pickups.py
Collectable items (ammo / keys) and the level exit portal.
"""
import math
import random
import pygame
from .constants import TILE, COLS, ROWS, C_AMMO, C_KEY, C_EXIT, C_DIM, C_BG, get_fonts
from .renderer  import draw_glowing_circle, draw_glowing_rect


class Item:
    """
    A collectable pick-up placed randomly in open maze cells.

    ``type`` is either ``"ammo"`` or ``"key"``.
    """

    def __init__(self, maze: list[list[int]], item_type: str,
                 hud_row: int = 2) -> None:
        self.type = item_type
        while True:
            x, y = random.randint(1, COLS - 2), random.randint(hud_row, ROWS - 2)
            if maze[y][x] == 0:
                break
        self.pos        = pygame.Vector2(x * TILE + 13, y * TILE + 13)
        self._bob_phase = random.uniform(0, math.tau)

    def draw(self, surf: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        t   = pygame.time.get_ticks() / 500
        bob = int(3 * math.sin(t + self._bob_phase))
        pos = (
            int(self.pos.x + camera_offset.x),
            int(self.pos.y + camera_offset.y) + bob,
        )
        fonts = get_fonts()
        if self.type == "ammo":
            draw_glowing_circle(surf, C_AMMO, pos, 7, 8)
            label = fonts["sm"].render("A", True, C_BG)
            surf.blit(label, (pos[0] - 4, pos[1] - 7))
        elif self.type == "key":
            draw_glowing_circle(surf, C_KEY, pos, 7, 8)
            label = fonts["sm"].render("K", True, C_BG)
            surf.blit(label, (pos[0] - 4, pos[1] - 7))
        elif self.type == "missile":
            # Orange glowing diamond
            col = (255, 120, 0)
            t2  = pygame.time.get_ticks() / 300
            bob2 = int(3 * math.sin(t2 + self._bob_phase))
            mpos = (pos[0], pos[1] + bob2 - int(3 * math.sin(self._bob_phase)))
            draw_glowing_circle(surf, col, mpos, 8, 10)
            # Arrow pointing right (missile shape)
            pts = [
                (mpos[0] - 8, mpos[1] - 3),
                (mpos[0] + 2, mpos[1] - 3),
                (mpos[0] + 8, mpos[1]),
                (mpos[0] + 2, mpos[1] + 3),
                (mpos[0] - 8, mpos[1] + 3),
            ]
            pygame.draw.polygon(surf, col, pts)
            pygame.draw.polygon(surf, (255, 220, 100), pts, 1)
            lbl = fonts["sm"].render("M", True, C_BG)
            surf.blit(lbl, (mpos[0] - 4, mpos[1] - 7))


class Exit:
    """
    The level-exit portal.  Remains locked until the player holds 5 keys.
    """

    REQUIRED_KEYS = 5

    def __init__(self, maze: list[list[int]], hud_row: int = 2) -> None:
        while True:
            x, y = random.randint(COLS // 2, COLS - 2), random.randint(max(ROWS // 2, hud_row), ROWS - 2)
            if maze[y][x] == 0:
                break
        self.pos  = pygame.Vector2(x * TILE + 13, y * TILE + 13)
        self.open = False

    def draw(self, surf: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        pos = (
            int(self.pos.x + camera_offset.x),
            int(self.pos.y + camera_offset.y),
        )
        col = C_EXIT if self.open else C_DIM
        t   = pygame.time.get_ticks() / 1000
        r   = int(14 + 3 * math.sin(t * 3)) if self.open else 14
        draw_glowing_rect(surf, col, (pos[0] - r, pos[1] - r, r * 2, r * 2),
                          2, 8 if self.open else 2)
        fonts = get_fonts()
        label = fonts["sm"].render("EXIT" if self.open else "LOCKED", True, col)
        surf.blit(label, (pos[0] - label.get_width() // 2, pos[1] + r + 4))
