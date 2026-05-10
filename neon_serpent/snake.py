"""
snake.py
Player-controlled snake entity.

Two-tier health system
-----------------------
HP (shield)  : 3 hit-points per life.  Damaged by bullets, laser, contact.
Lives        : 5 lives.  Deducted when HP hits 0 OR the snake hits a wall.

When a life is lost:
  - HP resets to MAX_HP
  - 5 s of immortality + wall-phase is granted  (flashing cyan)
  - lives == 0  →  caller receives True from take_hit() / lose_life()

Dash ability grants a separate 2 s invincibility + wall-phase.
"""
import math
import pygame
from .constants import TILE, COLS, ROWS, C_SNAKE_H, C_SNAKE_B, C_SNAKE_I, C_RED
from .renderer  import lerp_color
from .effects   import burst


class Snake:
    SPAWN_X       = TILE * 2 + 13
    SPAWN_Y       = TILE * 4 + 13   # below HUD solid border
    DASH_CD       = 5000
    DASH_PWR      = 130
    LIFE_IMMORTAL = 5000
    MAX_LIVES     = 10
    MAX_HP        = 3

    def __init__(self) -> None:
        self.head               = pygame.Vector2(self.SPAWN_X, self.SPAWN_Y)
        self.body               = [self.head.copy() for _ in range(16)]
        self.speed              = 1.3
        self.hp                 = self.MAX_HP
        self.max_hp             = self.MAX_HP
        self.lives              = self.MAX_LIVES
        self.max_lives          = self.MAX_LIVES
        self._last_dash         = -9999
        self._invincible_until  = 0
        self._phase_until       = 0
        self._life_immortal_until = 0
        self.trail: list = []

    # ── Combat ────────────────────────────────────────────────────────────────

    def take_hit(self, damage: int, particles: list, camera) -> bool:
        """Damage HP. Returns True if lives reach 0 (game over)."""
        if self.is_invincible():
            return False
        self.hp -= damage
        burst(particles, self.head.x, self.head.y, C_RED, 8, 3, 25)
        camera.shake(6)
        if self.hp <= 0:
            return self.lose_life(particles, camera)
        return False

    def lose_life(self, particles: list, camera) -> bool:
        """Instantly lose a life (wall hit). Returns True if game over."""
        if self.is_invincible():
            return False
        self.lives -= 1
        self.hp     = self.MAX_HP
        now = pygame.time.get_ticks()
        end = now + self.LIFE_IMMORTAL
        self._invincible_until    = end
        self._phase_until         = end
        self._life_immortal_until = end
        camera.shake(18)
        burst(particles, self.head.x, self.head.y, C_RED,     30, 5, 50)
        burst(particles, self.head.x, self.head.y, C_SNAKE_I, 20, 4, 40)
        return self.lives <= 0

    def is_life_immortal(self) -> bool:
        return pygame.time.get_ticks() < self._life_immortal_until

    def life_immortal_pct(self) -> float:
        remaining = self._life_immortal_until - pygame.time.get_ticks()
        return max(0.0, remaining / self.LIFE_IMMORTAL)

    def immortal_seconds_left(self) -> float:
        return max(0.0, (self._life_immortal_until - pygame.time.get_ticks()) / 1000)

    # ── Position reset (called on level entry) ───────────────────────────────

    def reset_position(self) -> None:
        """Teleport snake back to spawn point and clear body/trail."""
        self.head  = pygame.Vector2(self.SPAWN_X, self.SPAWN_Y)
        self.body  = [self.head.copy() for _ in range(16)]
        self.trail = []

    # ── Dash ──────────────────────────────────────────────────────────────────

    def dash(self, particles: list, camera) -> bool:
        now = pygame.time.get_ticks()
        if now - self._last_dash < self.DASH_CD:
            return False
        mx, my = pygame.mouse.get_pos()
        d = pygame.Vector2(mx, my) - self.head
        if d.length() == 0:
            return False
        self.head             += d.normalize() * self.DASH_PWR
        self._last_dash        = now
        self._invincible_until = max(self._invincible_until, now + 2000)
        self._phase_until      = max(self._phase_until, now + 2000)
        camera.shake(12)
        burst(particles, self.head.x, self.head.y, C_SNAKE_I, 20, 4, 40)
        return True

    def dash_cooldown_pct(self) -> float:
        return min(1.0, (pygame.time.get_ticks() - self._last_dash) / self.DASH_CD)

    def is_invincible(self) -> bool:
        return pygame.time.get_ticks() < self._invincible_until

    def can_phase(self) -> bool:
        return pygame.time.get_ticks() < self._phase_until

    # ── Movement ──────────────────────────────────────────────────────────────

    def move(self, maze: list) -> bool:
        """Returns True if wall hit (and not phasing)."""
        mx, my = pygame.mouse.get_pos()
        d = pygame.Vector2(mx, my) - self.head
        if d.length() > 1:
            self.head += d.normalize() * self.speed

        gx, gy = int(self.head.x // TILE), int(self.head.y // TILE)
        if not (0 <= gx < COLS and 0 <= gy < ROWS):
            return not self.can_phase()
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
        now = pygame.time.get_ticks()

        for i, t in enumerate(self.trail):
            alpha = int(60 * (i / max(1, len(self.trail))))
            s = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(s, (*C_SNAKE_H, alpha), (5, 5), 4)
            surf.blit(s, (int(t.x + camera_offset.x) - 5,
                          int(t.y + camera_offset.y) - 5))

        life_flicker = self.is_life_immortal() and (now // 120) % 2 == 0

        for i, b in enumerate(self.body):
            pct = 1 - i / len(self.body)
            r   = max(3, int(8 * pct))
            if life_flicker:
                color = lerp_color((20, 20, 60), C_SNAKE_I, pct)
            elif self.is_invincible():
                color = lerp_color(C_SNAKE_I, C_SNAKE_H, pct)
            else:
                color = lerp_color(C_SNAKE_B, C_SNAKE_H, pct)
            pos = (int(b.x + camera_offset.x), int(b.y + camera_offset.y))
            pygame.draw.circle(surf, color, pos, r)

        hpos = (int(self.head.x + camera_offset.x),
                int(self.head.y + camera_offset.y))

        if self.can_phase():
            pygame.draw.circle(surf, C_SNAKE_I, hpos, 16, 2)

        if self.is_life_immortal():
            pulse = int(20 + 5 * math.sin(now / 70))
            pygame.draw.circle(surf, C_RED, hpos, pulse, 2)
            pct   = self.life_immortal_pct()
            arc_r = pulse + 6
            rect  = pygame.Rect(hpos[0] - arc_r, hpos[1] - arc_r,
                                arc_r * 2, arc_r * 2)
            flash_col = (0, 220, 255) if (now // 200) % 2 == 0 else (0, 120, 180)
            end_angle = math.radians(90 + 360 * pct)
            if end_angle > math.radians(91):
                pygame.draw.arc(surf, flash_col, rect,
                                math.radians(90), end_angle, 3)
