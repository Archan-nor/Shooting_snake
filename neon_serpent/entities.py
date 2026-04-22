"""
entities.py
Enemy and Boss classes.
"""
import math
import random
import pygame
from .constants import (
    TILE, COLS, ROWS,
    C_ENEMY, C_BOSS, C_BOSS_PROJ, C_AMMO, C_HUD_BORDER, C_WHITE, W, H,
)
from .renderer  import draw_glowing_circle
from .effects   import burst
from .bullet    import Bullet


# ── Enemy ─────────────────────────────────────────────────────────────────────

class Enemy:
    """
    A basic ranged enemy that chases the player and fires projectiles.
    Flees briefly after taking a hit.
    """

    def __init__(self, maze: list[list[int]]) -> None:
        while True:
            x, y = random.randint(5, COLS - 2), random.randint(5, ROWS - 2)
            if maze[y][x] == 0:
                break
        self.pos        = pygame.Vector2(x * TILE + 13, y * TILE + 13)
        self.speed      = random.uniform(0.7, 1.1)
        self.hp         = 3
        self.max_hp     = 3
        self._flee      = 0
        self._shoot_cd  = random.randint(120, 300)
        self._shoot_t   = random.randint(0, 200)
        self._angle     = 0.0

    def update(self, player_head: pygame.Vector2, bullets: list) -> None:
        d    = player_head - self.pos
        dist = d.length()

        if self._flee > 0:
            self._flee -= 1
            if dist > 0:
                self.pos -= d.normalize() * self.speed
        else:
            if dist < 180:
                self.pos += d.normalize() * self.speed
            else:
                self.pos += pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))

        self._shoot_t -= 1
        if self._shoot_t <= 0 and dist < 250:
            bullets.append(
                Bullet(self.pos, player_head, speed=4, color=(255, 100, 80), damage=1)
            )
            self._shoot_t = self._shoot_cd

        self._angle += 3

    def hit(self, particles: list) -> None:
        self.hp    -= 1
        self._flee  = 60
        burst(particles, self.pos.x, self.pos.y, C_ENEMY, 8, 3)

    def draw(self, surf: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        pos = (
            int(self.pos.x + camera_offset.x),
            int(self.pos.y + camera_offset.y),
        )
        for i in range(3):
            a  = math.radians(self._angle + i * 120)
            px = pos[0] + int(10 * math.cos(a))
            py = pos[1] + int(10 * math.sin(a))
            draw_glowing_circle(surf, C_ENEMY, (px, py), 4, 4)
        draw_glowing_circle(surf, C_ENEMY, pos, 7, 6)
        # Mini HP bar
        bx, by = pos[0] - 14, pos[1] - 20
        pygame.draw.rect(surf, (40, 0, 0),  (bx, by, 28,  4), border_radius=2)
        pygame.draw.rect(surf, C_ENEMY,     (bx, by, int(28 * self.hp / self.max_hp), 4), border_radius=2)


# ── Boss ──────────────────────────────────────────────────────────────────────

class Boss:
    """
    Three-phase final boss.

    Phase 0 – spiral bullet spread
    Phase 1 – aimed burst, orbiting shield, minion summons
    Phase 2 – dense spiral, charging laser beam
    """

    PHASE_NAMES = ["AWAKENING", "ENRAGED", "FINAL FORM"]

    def __init__(self, maze: list[list[int]]) -> None:
        cx, cy = COLS // 2, ROWS // 2
        for y in range(cy - 3, cy + 3):
            for x in range(cx - 3, cx + 3):
                maze[y][x] = 0
        self.pos        = pygame.Vector2(cx * TILE, cy * TILE)
        self.hp         = 120
        self.max_hp     = 120
        self._phase     = 0
        self._angle     = 0.0
        self._orb_angle = 0.0
        self._shoot_t   = 0
        self._move_t    = 0
        self._target    = self.pos.copy()
        self.speed      = 1.0
        self._enrage_flash = 0
        self._summon_t  = 0
        self.orbs       = 0
        self.shield     = 0
        self.shield_max = 0
        self._laser_charge  = 0
        self.laser_firing   = False
        self._laser_dir     = pygame.Vector2(1, 0)
        self._laser_timer   = 0
        self.dead           = False
        self._death_timer   = 0

    # ── Phase property ────────────────────────────────────────────────────────

    @property
    def phase(self) -> int:
        return self._phase

    @phase.setter
    def phase(self, v: int) -> None:
        self._phase = v
        if v == 1:
            self.hp         = int(self.max_hp * 0.66)
            self.speed      = 1.5
            self.orbs       = 6
            self.shield     = 20
            self.shield_max = 20
        elif v == 2:
            self.hp         = int(self.max_hp * 0.33)
            self.speed      = 2.2
            self.orbs       = 0
            self._laser_charge = 0

    def _get_phase(self) -> int:
        if self.hp > self.max_hp * 0.66:
            return 0
        if self.hp > self.max_hp * 0.33:
            return 1
        return 2

    # ── Update ────────────────────────────────────────────────────────────────

    def update(
        self,
        player_head: pygame.Vector2,
        bullets: list,
        enemies: list,
        maze: list[list[int]],
        particles: list,
        camera,
    ) -> None:
        if self.dead:
            self._death_timer += 1
            burst(
                particles,
                self.pos.x + random.uniform(-30, 30),
                self.pos.y + random.uniform(-30, 30),
                C_BOSS, 4, 5, 40,
            )
            return

        new_phase = self._get_phase()
        if new_phase != self._phase:
            self.phase = new_phase
            camera.shake(20)
            burst(particles, self.pos.x, self.pos.y, C_BOSS, 40, 6, 60)
            self._enrage_flash = 60

        if self._enrage_flash > 0:
            self._enrage_flash -= 1

        self._angle     += 1.5 + self._phase * 0.5
        self._orb_angle += 2.0 + self._phase

        # Movement toward player
        self._move_t -= 1
        if self._move_t <= 0:
            d = player_head - self.pos
            if d.length() > 0:
                self._target = self.pos + d.normalize() * random.uniform(60, 120)
            self._move_t = random.randint(60, 120)
        mv = self._target - self.pos
        if mv.length() > 1:
            self.pos += mv.normalize() * self.speed

        d_to_player = player_head - self.pos
        dist        = d_to_player.length()

        # ── Attack patterns ──────────────────────────────────────────────────

        if self._phase == 0:                       # spiral
            self._shoot_t -= 1
            if self._shoot_t <= 0:
                for i in range(8):
                    a   = math.radians(self._angle + i * 45)
                    vel = pygame.Vector2(math.cos(a) * 5, math.sin(a) * 5)
                    b   = Bullet(self.pos, self.pos + vel * 10, speed=5,
                                 color=C_BOSS_PROJ, damage=1, is_boss=True)
                    b.vel = vel
                    bullets.append(b)
                self._shoot_t = 40

        elif self._phase == 1:                     # aimed burst + summon
            self._shoot_t -= 1
            if self._shoot_t <= 0:
                for i in range(-2, 3):
                    a   = math.atan2(d_to_player.y, d_to_player.x) + math.radians(i * 15)
                    vel = pygame.Vector2(math.cos(a) * 6, math.sin(a) * 6)
                    b   = Bullet(self.pos, self.pos + vel * 10, speed=6,
                                 color=C_BOSS_PROJ, damage=1, is_boss=True)
                    b.vel = vel
                    bullets.append(b)
                self._shoot_t = 55
            self._summon_t -= 1
            if self._summon_t <= 0 and len(enemies) < 6:
                from .entities import Enemy          # lazy to avoid circular
                enemies.append(Enemy(maze))
                self._summon_t = 300

        elif self._phase == 2:                     # dense spiral + laser
            self._shoot_t -= 1
            if self._shoot_t <= 0:
                for i in range(12):
                    a   = math.radians(self._angle + i * 30)
                    vel = pygame.Vector2(math.cos(a) * 7, math.sin(a) * 7)
                    b   = Bullet(self.pos, self.pos + vel * 10, speed=7,
                                 color=(255, 0, 200), damage=1, is_boss=True)
                    b.vel = vel
                    bullets.append(b)
                self._shoot_t = 25

            if not self.laser_firing:
                self._laser_charge += 1
                if self._laser_charge >= 200:
                    self.laser_firing  = True
                    self._laser_dir    = (
                        d_to_player.normalize() if dist > 0 else pygame.Vector2(1, 0)
                    )
                    self._laser_timer  = 90
                    camera.shake(8)
            else:
                target_a = math.atan2(d_to_player.y, d_to_player.x)
                cur_a    = math.atan2(self._laser_dir.y, self._laser_dir.x)
                diff     = (target_a - cur_a + math.pi) % (2 * math.pi) - math.pi
                cur_a   += max(-0.02, min(0.02, diff))
                self._laser_dir = pygame.Vector2(math.cos(cur_a), math.sin(cur_a))
                self._laser_timer -= 1
                if self._laser_timer <= 0:
                    self.laser_firing  = False
                    self._laser_charge = 0

    # ── Combat ────────────────────────────────────────────────────────────────

    def take_damage(self, dmg: int, particles: list, camera) -> None:
        if self.shield > 0:
            self.shield -= dmg
            burst(particles, self.pos.x, self.pos.y, C_HUD_BORDER, 6, 3)
            return
        self.hp -= dmg
        burst(particles, self.pos.x, self.pos.y, C_BOSS, 10, 4)
        camera.shake(6)
        if self.hp <= 0:
            self.hp   = 0
            self.dead = True

    def check_laser_hit(self, player_head: pygame.Vector2) -> bool:
        if not self.laser_firing:
            return False
        v   = player_head - self.pos
        t   = v.dot(self._laser_dir)
        if t < 0:
            return False
        closest = self.pos + self._laser_dir * t
        return (player_head - closest).length() < 14

    @property
    def death_timer(self) -> int:
        return self._death_timer

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surf: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        pos = (
            int(self.pos.x + camera_offset.x),
            int(self.pos.y + camera_offset.y),
        )
        now = pygame.time.get_ticks()

        # Death animation
        if self.dead:
            t     = min(1.0, self._death_timer / 120)
            r     = int(40 + 60 * t)
            alpha = int(255 * (1 - t))
            s     = pygame.Surface((r * 2 + 10, r * 2 + 10), pygame.SRCALPHA)
            pygame.draw.circle(s, (*C_BOSS, alpha), (r + 5, r + 5), r)
            surf.blit(s, (pos[0] - r - 5, pos[1] - r - 5))
            return

        col = [C_BOSS, (220, 50, 255), (255, 0, 180)][self._phase]
        if self._enrage_flash > 0 and self._enrage_flash % 6 < 3:
            col = C_WHITE

        # Shield ring
        if self.shield > 0:
            for i in range(12):
                a  = math.radians(self._orb_angle * 2 + i * 30)
                sx = pos[0] + int(32 * math.cos(a))
                sy = pos[1] + int(32 * math.sin(a))
                draw_glowing_circle(surf, C_AMMO, (sx, sy), 4, 4)

        # Orbiting orbs
        for i in range(self.orbs):
            a  = math.radians(self._orb_angle + i * (360 // max(1, self.orbs)))
            ox = pos[0] + int(45 * math.cos(a))
            oy = pos[1] + int(45 * math.sin(a))
            draw_glowing_circle(surf, (255, 100, 255), (ox, oy), 5, 6)

        # Laser charge indicator
        if self._phase == 2 and not self.laser_firing:
            pct = self._laser_charge / 200
            for i in range(int(pct * 16)):
                a  = math.radians(i * 22.5 + now * 0.1)
                lx = pos[0] + int((20 + pct * 10) * math.cos(a))
                ly = pos[1] + int((20 + pct * 10) * math.sin(a))
                pygame.draw.circle(surf, (255, int(255 * (1 - pct)), 0), (lx, ly), 3)

        # Laser beam
        if self.laser_firing:
            end = self.pos + self._laser_dir * 800
            ep  = (
                int(end.x + camera_offset.x),
                int(end.y + camera_offset.y),
            )
            for width in [10, 6, 3]:
                alpha = 180 if width == 10 else (220 if width == 6 else 255)
                s     = pygame.Surface((W, H), pygame.SRCALPHA)
                pygame.draw.line(s, (*col, alpha), pos, ep, width)
                surf.blit(s, (0, 0))

        # Rotating outer polygon
        sides = 6 + self._phase
        pts   = []
        for i in range(sides):
            a = math.radians(self._angle + i * (360 // sides))
            pts.append((pos[0] + int(24 * math.cos(a)), pos[1] + int(24 * math.sin(a))))
        if len(pts) >= 3:
            pygame.draw.polygon(surf, col, pts, 2)

        # Core
        draw_glowing_circle(surf, col, pos, 16, 14)
        pygame.draw.circle(surf, C_WHITE, pos, 8)
