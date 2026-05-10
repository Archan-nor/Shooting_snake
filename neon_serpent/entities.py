"""
entities.py
Enemy and Boss classes.

Boss changes
------------
- Knockback 1 s when hit
- Phase 0 start: spawn 4 missiles + 5 ammo, no enemies
- Phase 0→1: spawn 4 missiles + 5 ammo + 6 enemies immediately
- Phase 1→2: spawn 4 missiles
- Phase 1+: summon 2 enemies every 300 frames if < 4
- ammo_spawn_active flag passed back via game dict (set True on phase 1)
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
    def __init__(self, maze: list[list[int]], hud_row: int = 2) -> None:
        while True:
            x, y = random.randint(5, COLS - 2), random.randint(max(5, hud_row), ROWS - 2)
            if maze[y][x] == 0:
                break
        self.pos       = pygame.Vector2(x * TILE + 13, y * TILE + 13)
        self.speed     = random.uniform(0.7, 1.1)
        self.hp        = 3
        self.max_hp    = 3
        self._flee     = 0
        self._shoot_cd = random.randint(120, 300)
        self._shoot_t  = random.randint(0, 200)
        self._angle    = 0.0

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
        self.hp   -= 1
        self._flee = 60
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
        bx, by = pos[0] - 14, pos[1] - 20
        pygame.draw.rect(surf, (40, 0, 0), (bx, by, 28, 4), border_radius=2)
        pygame.draw.rect(surf, C_ENEMY,
                         (bx, by, int(28 * self.hp / self.max_hp), 4), border_radius=2)


# ── Boss ──────────────────────────────────────────────────────────────────────

class Boss:
    PHASE_NAMES = ["AWAKENING", "ENRAGED", "FINAL FORM"]
    KNOCKBACK_DURATION = 300    # ms (0.3 s)

    def __init__(self, maze: list[list[int]]) -> None:
        cx, cy = COLS // 2, ROWS // 2
        for y in range(cy - 3, cy + 3):
            for x in range(cx - 3, cx + 3):
                maze[y][x] = 0
        self.pos             = pygame.Vector2(cx * TILE, cy * TILE)
        self.hp              = 120
        self.max_hp          = 120
        self._phase          = 0
        self._angle          = 0.0
        self._orb_angle      = 0.0
        self._shoot_t        = 0
        self._move_t         = 0
        self._target         = self.pos.copy()
        self.speed           = 1.0
        self._enrage_flash   = 0
        self._summon_t       = 0
        self.orbs            = 0
        self.shield          = 0
        self.shield_max      = 0
        self._laser_charge   = 0    # kept for compatibility
        self.laser_firing    = False
        self._laser_dir      = pygame.Vector2(1, 0)
        self._laser_timer    = 0
        # Rifle (phase 2)
        self._rifle_timer     = 0
        self._rifle_aiming    = False
        self._rifle_aim_timer = 0
        self._rifle_dir       = pygame.Vector2(1, 0)
        self.dead            = False
        self._death_timer    = 0
        # Knockback
        self._knockback_until = 0
        self._knockback_dir   = pygame.Vector2(0, 0)
        # Spawn-event flags (read by main.py, then cleared)
        self.spawn_events: list[str] = []   # e.g. ["missile","ammo","enemies6"]

    # ── Phase property ────────────────────────────────────────────────────────

    @property
    def phase(self) -> int:
        return self._phase

    @phase.setter
    def phase(self, v: int) -> None:
        self._phase = v
        if v == 1:
            # NOTE: don't reset HP — preserve current HP so boss can keep losing
            self.speed      = 1.5
            self.orbs       = 6
            # No shield in phase 1
            self.shield     = 0
            self.shield_max = 0
            # Summon 2 enemies immediately, enable ammo spawn
            self.spawn_events += ["missile4", "ammo5", "enemies2",
                                  "ammo_spawn_on", "phase_change_1"]
        elif v == 2:
            self.speed            = 2.2
            self.orbs             = 0
            self._rifle_timer     = 0
            self._rifle_aiming    = False
            self._rifle_aim_timer = 0
            self._rifle_dir       = pygame.Vector2(1, 0)
            self.spawn_events    += ["missile4", "phase_change_2"]

    def _get_phase(self) -> int:
        # Phase 0: 120-81, Phase 1: 80-41, Phase 2: 40-0
        if self.hp > 80:
            return 0
        if self.hp > 40:
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

        now = pygame.time.get_ticks()

        # Phase transition check (phases only increase 0→1→2, never back)
        new_phase = self._get_phase()
        if new_phase > self._phase:
            self.phase = new_phase
            self._enrage_flash = 30

        if self._enrage_flash > 0:
            self._enrage_flash -= 1

        self._angle     += 1.5 + self._phase * 0.5
        self._orb_angle += 2.0 + self._phase

        # ── Movement (skip normal move during knockback) ───────────────────
        if now < self._knockback_until:
            self.pos += self._knockback_dir * 2.5
        else:
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

        # ── Attack patterns ───────────────────────────────────────────────
        if self._phase == 0:
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

        elif self._phase == 1:
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
            # Summon 2 enemies every 300 frames if < 4
            self._summon_t -= 1
            if self._summon_t <= 0 and len(enemies) < 4:
                for _ in range(2):
                    enemies.append(Enemy(maze))
                self._summon_t = 300

        elif self._phase == 2:
            # Dense spiral
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
            # Summon 2 enemies every 300 frames if < 4
            self._summon_t -= 1
            if self._summon_t <= 0 and len(enemies) < 4:
                for _ in range(2):
                    enemies.append(Enemy(maze))
                self._summon_t = 300
            # ── Rifle: every 20 s aim for 4 s then fire pierce bullet ────────
            FPS        = 60
            AIM_FRAMES = 3 * FPS    # 3 s aim
            COOLDOWN   = 13 * FPS   # 13 s between shots
            if not self._rifle_aiming:
                self._rifle_timer += 1
                if self._rifle_timer >= COOLDOWN:
                    self._rifle_aiming    = True
                    self._rifle_aim_timer = AIM_FRAMES
                    self._rifle_dir       = (
                        d_to_player.normalize() if dist > 0 else pygame.Vector2(1, 0)
                    )
                    camera.shake(4)
            else:
                # Rotate aim line toward player every frame
                if dist > 0:
                    target_a = math.atan2(d_to_player.y, d_to_player.x)
                    cur_a    = math.atan2(self._rifle_dir.y, self._rifle_dir.x)
                    diff     = (target_a - cur_a + math.pi) % (2 * math.pi) - math.pi
                    cur_a   += max(-0.03, min(0.03, diff))
                    self._rifle_dir = pygame.Vector2(math.cos(cur_a), math.sin(cur_a))
                self._rifle_aim_timer -= 1
                if self._rifle_aim_timer <= 0:
                    # Fire pierce bullet
                    rifle_speed = 10 * 1.5
                    rb = Bullet(
                        self.pos,
                        self.pos + self._rifle_dir * 10,
                        speed=rifle_speed,
                        color=(255, 50, 50),
                        damage=2,
                        is_boss=True,
                        pierce_wall=True,
                    )
                    rb.vel = self._rifle_dir * rifle_speed
                    bullets.append(rb)
                    camera.shake(10)
                    self._rifle_aiming = False
                    self._rifle_timer  = 0

    # ── Combat ────────────────────────────────────────────────────────────────

    def take_damage(self, dmg: int, particles: list, camera,
                    player_head: pygame.Vector2 | None = None) -> None:
        if self.shield > 0:
            self.shield -= dmg
            burst(particles, self.pos.x, self.pos.y, C_HUD_BORDER, 6, 3)
            return
        self.hp = max(0, self.hp - dmg)
        burst(particles, self.pos.x, self.pos.y, C_BOSS, 10, 4)
        camera.shake(6)
        # Knockback away from player
        if player_head is not None:
            d = self.pos - player_head
            if d.length() > 0:
                self._knockback_dir   = d.normalize()
                self._knockback_until = pygame.time.get_ticks() + self.KNOCKBACK_DURATION
        if self.hp <= 0:
            self.hp   = 0
            self.dead = True

    def check_laser_hit(self, player_head: pygame.Vector2) -> bool:
        """Laser removed — rifle uses normal bullet collision."""
        return False

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

        # Knockback flash
        if pygame.time.get_ticks() < self._knockback_until:
            if (now // 80) % 2 == 0:
                col = (255, 255, 100)

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

        # Rifle aim line (phase 2 only)
        if self._phase == 2 and self._rifle_aiming:
            end   = self.pos + self._rifle_dir * 900
            ep    = (int(end.x + camera_offset.x), int(end.y + camera_offset.y))
            flash = (now // 150) % 2 == 0
            # Dashed red aim line
            aim_col = (255, 0, 0) if flash else (180, 0, 0)
            seg_len, gap = 18, 8
            total  = int((end - self.pos).length())
            drawn  = 0
            while drawn < total:
                t0 = drawn / total
                t1 = min((drawn + seg_len) / total, 1.0)
                p0 = (int(self.pos.x + camera_offset.x + self._rifle_dir.x * drawn),
                      int(self.pos.y + camera_offset.y + self._rifle_dir.y * drawn))
                p1 = (int(self.pos.x + camera_offset.x + self._rifle_dir.x * (drawn + seg_len)),
                      int(self.pos.y + camera_offset.y + self._rifle_dir.y * (drawn + seg_len)))
                pygame.draw.line(surf, aim_col, p0, p1, 2)
                drawn += seg_len + gap
            # Countdown ring around boss
            pct  = self._rifle_aim_timer / (4 * 60)
            arc_r = 30
            rect  = pygame.Rect(pos[0] - arc_r, pos[1] - arc_r, arc_r * 2, arc_r * 2)
            if pct > 0:
                pygame.draw.arc(surf, (255, 80, 80), rect,
                                math.radians(90),
                                math.radians(90 + 360 * pct), 3)

        # Rotating polygon
        sides = 6 + self._phase
        pts   = []
        for i in range(sides):
            a = math.radians(self._angle + i * (360 // sides))
            pts.append((pos[0] + int(24 * math.cos(a)), pos[1] + int(24 * math.sin(a))))
        if len(pts) >= 3:
            pygame.draw.polygon(surf, col, pts, 2)

        draw_glowing_circle(surf, col, pos, 16, 14)
        pygame.draw.circle(surf, C_WHITE, pos, 8)