"""
effects.py
Camera shake and particle-burst visual effects.
"""
import math
import random
import pygame
from .constants import C_AMMO


# ── Camera ───────────────────────────────────────────────────────────────────

class Camera:
    """Applies a screen-shake offset to every world-space draw call."""

    def __init__(self) -> None:
        self.offset    = pygame.Vector2(0, 0)
        self.intensity = 0.0

    def shake(self, power: float) -> None:
        """Queue a shake of given pixel intensity."""
        self.intensity = max(self.intensity, power)

    def update(self) -> None:
        if self.intensity > 0.3:
            self.offset.x  = random.uniform(-self.intensity, self.intensity)
            self.offset.y  = random.uniform(-self.intensity, self.intensity)
            self.intensity *= 0.82
        else:
            self.offset    = pygame.Vector2(0, 0)
            self.intensity = 0.0


# ── Particle ─────────────────────────────────────────────────────────────────

class Particle:
    """A single spark emitted by explosions and hits."""

    def __init__(
        self,
        x: float, y: float,
        color: tuple = C_AMMO,
        speed: float = 3.0,
        life: int    = 30,
    ) -> None:
        self.pos      = pygame.Vector2(x, y)
        angle         = random.uniform(0, math.tau)
        spd           = random.uniform(0.5, speed)
        self.vel      = pygame.Vector2(math.cos(angle) * spd, math.sin(angle) * spd)
        self.life     = life
        self.max_life = life
        self.color    = color
        self.size     = random.randint(2, 5)

    def update(self) -> None:
        self.pos += self.vel
        self.vel *= 0.93
        self.life -= 1

    def draw(self, surf: pygame.Surface, camera: "Camera") -> None:
        if self.life <= 0:
            return
        t     = self.life / self.max_life
        r     = int(self.size * t)
        alpha = int(200 * t)
        if r < 1:
            return
        s = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (r + 1, r + 1), r)
        surf.blit(
            s,
            (int(self.pos.x + camera.offset.x) - r - 1,
             int(self.pos.y + camera.offset.y) - r - 1),
        )


# ── Particle manager helper ───────────────────────────────────────────────────

def burst(
    particles: list,
    x: float, y: float,
    color: tuple,
    n: int   = 12,
    speed: float = 3.0,
    life: int    = 30,
) -> None:
    """Append *n* fresh particles at (x, y) into *particles*."""
    for _ in range(n):
        particles.append(Particle(x, y, color, speed, life))
