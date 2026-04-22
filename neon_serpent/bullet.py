"""
bullet.py
Projectile fired by both the player and enemies / the boss.
"""
import pygame
from .constants import TILE, COLS, ROWS, C_BULLET
from .renderer  import draw_glowing_circle


class Bullet:
    """
    A single fast-moving projectile.

    Parameters
    ----------
    pos      : starting (x, y) in world-pixels
    target   : (x, y) the bullet travels toward
    speed    : pixels per frame
    color    : RGB tuple
    damage   : HP deducted on hit
    is_boss  : True if fired by the boss (used for collision filtering)
    """

    def __init__(
        self,
        pos: tuple,
        target: tuple,
        speed: float  = 10.0,
        color: tuple  = C_BULLET,
        damage: int   = 1,
        is_boss: bool = False,
    ) -> None:
        self.pos    = pygame.Vector2(pos)
        d           = pygame.Vector2(target) - self.pos
        self.vel    = d.normalize() * speed if d.length() > 0 else pygame.Vector2(speed, 0)
        self.life   = 80
        self.color  = color
        self.damage = damage
        self.is_boss = is_boss

    def update(self, maze: list[list[int]]) -> bool:
        """Move one step.  Returns True when the bullet should be removed."""
        self.pos  += self.vel
        self.life -= 1
        gx, gy = int(self.pos.x // TILE), int(self.pos.y // TILE)
        if not (0 <= gx < COLS and 0 <= gy < ROWS):
            return True
        if maze[gy][gx] == 1:
            return True
        return self.life <= 0

    def draw(self, surf: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        p = (
            int(self.pos.x + camera_offset.x),
            int(self.pos.y + camera_offset.y),
        )
        draw_glowing_circle(surf, self.color, p, 4, 5)
