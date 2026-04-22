"""
snake.py
Player-controlled snake entity.
"""
import pygame
from .constants import TILE, COLS, ROWS, C_SNAKE_H, C_SNAKE_B, C_SNAKE_I
from .renderer  import lerp_color
from .effects   import burst


class Snake:
    """
    The player character.

    Movement is mouse-following; the body is a list of historical head
    positions.  The dash ability grants short-range teleport plus
    temporary invincibility and wall-phase.
    """

    SPAWN_X = TILE * 2 + 13
    SPAWN_Y = TILE * 2 + 13
    DASH_CD  = 5000          # milliseconds
    DASH_PWR = 130           # pixels

    def __init__(self) -> None:
        self.head             = pygame.Vector2(self.SPAWN_X, self.SPAWN_Y)
        self.body             = [self.head.copy() for _ in range(16)]
        self.speed            = 1.3
        self.hp               = 5
        self.max_hp           = 5
        self._last_dash       = -9999
        self._invincible_until = 0
        self._phase_until     = 0
        self.trail: list[pygame.Vector2] = []

    # ── Abilities ─────────────────────────────────────────────────────────────

    def dash(self, particles: list, camera) -> bool:
        """
        Teleport toward cursor.  Returns True if the dash fired.
        Grants 2 s of invincibility and wall-phase.
        """
        now = pygame.time.get_ticks()
        if now - self._last_dash < self.DASH_CD:
            return False
        mx, my = pygame.mouse.get_pos()
        d = pygame.Vector2(mx, my) - self.head
        if d.length() == 0:
            return False
        self.head            += d.normalize() * self.DASH_PWR
        self._last_dash       = now
        self._invincible_until = now + 2000
        self._phase_until     = now + 2000
        camera.shake(12)
        burst(particles, self.head.x, self.head.y, C_SNAKE_I, 20, 4, 40)
        return True

    def dash_cooldown_pct(self) -> float:
        """0.0 = on cooldown, 1.0 = ready."""
        elapsed = pygame.time.get_ticks() - self._last_dash
        return min(1.0, elapsed / self.DASH_CD)

    def is_invincible(self) -> bool:
        return pygame.time.get_ticks() < self._invincible_until

    def can_phase(self) -> bool:
        return pygame.time.get_ticks() < self._phase_until

    # ── Update ────────────────────────────────────────────────────────────────

    def move(self, maze: list[list[int]]) -> bool:
        """
        Follow the mouse cursor.
        Returns True if the snake hit a wall (game-over condition).
        """
        mx, my = pygame.mouse.get_pos()
        d = pygame.Vector2(mx, my) - self.head
        if d.length() > 1:
            self.head += d.normalize() * self.speed

        gx, gy = int(self.head.x // TILE), int(self.head.y // TILE)
        if not (0 <= gx < COLS and 0 <= gy < ROWS):
            return True
        if maze[gy][gx] == 1 and not self.can_phase():
            return True

        self.trail.append(self.head.copy())
        if len(self.trail) > 8:
            self.trail.pop(0)
        self.body.insert(0, self.head.copy())
        self.body.pop()
        return False

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surf: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        # Ghost trail
        for i, t in enumerate(self.trail):
            alpha = int(60 * (i / max(1, len(self.trail))))
            s = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(s, (*C_SNAKE_H, alpha), (5, 5), 4)
            surf.blit(s, (int(t.x + camera_offset.x) - 5,
                          int(t.y + camera_offset.y) - 5))

        # Body segments
        for i, b in enumerate(self.body):
            pct   = 1 - i / len(self.body)
            r     = max(3, int(8 * pct))
            color = lerp_color(C_SNAKE_B, C_SNAKE_H, pct)
            if self.is_invincible():
                color = lerp_color(C_SNAKE_I, C_SNAKE_H, pct)
            pos = (int(b.x + camera_offset.x), int(b.y + camera_offset.y))
            pygame.draw.circle(surf, color, pos, r)

        # Head ring when phasing
        if self.can_phase():
            hpos = (int(self.head.x + camera_offset.x),
                    int(self.head.y + camera_offset.y))
            pygame.draw.circle(surf, C_SNAKE_I, hpos, 16, 2)
