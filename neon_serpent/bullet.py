"""
bullet.py
Projectile fired by both the player and enemies / the boss.

pierce_wall=True  → rifle bullet that ignores maze walls (boss phase 2 only)
"""
import pygame
from .constants import TILE, COLS, ROWS, C_BULLET
from .renderer  import draw_glowing_circle


class Bullet:
    def __init__(
        self,
        pos: tuple,
        target: tuple,
        speed: float      = 10.0,
        color: tuple      = C_BULLET,
        damage: int       = 1,
        is_boss: bool     = False,
        pierce_wall: bool = False,   # rifle bullet only
    ) -> None:
        self.pos         = pygame.Vector2(pos)
        d                = pygame.Vector2(target) - self.pos
        self.vel         = d.normalize() * speed if d.length() > 0 else pygame.Vector2(speed, 0)
        self.life        = 120 if pierce_wall else 80   # rifle travels further
        self.color       = color
        self.damage      = damage
        self.is_boss     = is_boss
        self.pierce_wall = pierce_wall

    def update(self, maze: list[list[int]]) -> bool:
        """Move one step. Returns True when bullet should be removed."""
        self.pos  += self.vel
        self.life -= 1
        gx, gy = int(self.pos.x // TILE), int(self.pos.y // TILE)
        if not (0 <= gx < COLS and 0 <= gy < ROWS):
            return True
        # Only non-pierce bullets are blocked by walls
        if not self.pierce_wall and maze[gy][gx] == 1:
            return True
        return self.life <= 0

    def draw(self, surf: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        p = (
            int(self.pos.x + camera_offset.x),
            int(self.pos.y + camera_offset.y),
        )
        r = 5 if self.pierce_wall else 4
        draw_glowing_circle(surf, self.color, p, r, 6 if self.pierce_wall else 5)
