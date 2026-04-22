"""
main.py
Entry point – initialises pygame, owns the main game loop,
delegates everything else to the neon_serpent package.
"""
import pygame

from neon_serpent.constants import W, H, C_BG, C_SNAKE_H, C_RED, C_BOSS, get_fonts
from neon_serpent.effects   import Camera, burst
from neon_serpent.bullet    import Bullet
from neon_serpent.level     import new_game, new_level
from neon_serpent.hud       import draw_hud, draw_menu, draw_death, draw_win, draw_boss_intro

pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("NEON SERPENT")
clock  = pygame.time.Clock()

# ── Shared state ──────────────────────────────────────────────────────────────
camera         = Camera()
particles: list = []
bullets:   list = []          # player bullets
enemy_bullets: list = []      # enemy / boss bullets

scene       = "menu"
game        = None
death_time  = 0
death_cause = ""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _clear_projectiles() -> None:
    bullets.clear()
    enemy_bullets.clear()
    particles.clear()


# ── Main loop ─────────────────────────────────────────────────────────────────
running = True
while running:
    screen.fill(C_BG)
    camera.update()
    now = pygame.time.get_ticks()

    # ── Events ────────────────────────────────────────────────────────────────
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif scene == "menu":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                game = new_game()
                _clear_projectiles()
                scene = "game"

        elif scene == "win":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                scene = "menu"

        elif scene == "death":
            if now - death_time > 3000:
                scene = "menu"

        elif scene == "game":
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and game["ammo"] > 0:
                    bullets.append(
                        Bullet(game["snake"].head, pygame.mouse.get_pos(), speed=10)
                    )
                    game["ammo"] -= 1
                if event.button == 3:
                    game["snake"].dash(particles, camera)

    # ── Update ────────────────────────────────────────────────────────────────
    if scene == "game":
        snake   = game["snake"]
        maze    = game["maze"]
        boss    = game.get("boss")
        elapsed = (now - game["start"]) / 1000
        started = elapsed > 3

        if game["boss_intro"] > 0:
            game["boss_intro"] -= 1
            started = False

        if started:
            # ── Snake movement ───────────────────────────────────────────────
            if snake.move(maze):
                scene       = "death"
                death_cause = "WALL COLLISION"
                death_time  = now
                camera.shake(15)

            # ── Enemy bullets hit snake ──────────────────────────────────────
            for b in enemy_bullets[:]:
                if b.update(maze):
                    enemy_bullets.remove(b)
                    continue
                if (pygame.Vector2(b.pos) - snake.head).length() < 12 and not snake.is_invincible():
                    snake.hp -= b.damage
                    enemy_bullets.remove(b)
                    camera.shake(8)
                    burst(particles, snake.head.x, snake.head.y, C_RED, 10, 3)
                    if snake.hp <= 0:
                        scene       = "death"
                        death_cause = "OVERWHELMED BY ENEMIES"
                        death_time  = now
                    continue

            # ── Boss laser ───────────────────────────────────────────────────
            if boss and not boss.dead:
                if boss.check_laser_hit(snake.head) and not snake.is_invincible():
                    snake.hp -= 1
                    camera.shake(5)
                    burst(particles, snake.head.x, snake.head.y, C_BOSS, 6, 3)
                    if snake.hp <= 0:
                        scene       = "death"
                        death_cause = "INCINERATED BY LASER"
                        death_time  = now

            # ── Enemy contact damage ─────────────────────────────────────────
            for en in game["enemies"]:
                if (en.pos - snake.head).length() < 16 and not snake.is_invincible():
                    snake.hp -= 1
                    camera.shake(8)
                    burst(particles, snake.head.x, snake.head.y, C_RED, 8, 3)
                    if snake.hp <= 0:
                        scene       = "death"
                        death_cause = "CONSUMED BY ENEMIES"
                        death_time  = now

            # ── Update enemies ───────────────────────────────────────────────
            for en in game["enemies"]:
                en.update(snake.head, enemy_bullets)

            # ── Update boss ──────────────────────────────────────────────────
            if boss and not boss.dead:
                boss.update(snake.head, enemy_bullets, game["enemies"], maze, particles, camera)

        # ── Player bullets hit enemies / boss ────────────────────────────────
        for b in bullets[:]:
            if b.update(maze):
                bullets.remove(b)
                continue
            hit = False
            for en in game["enemies"][:]:
                if (en.pos - b.pos).length() < 14:
                    en.hit(particles)
                    if en.hp <= 0:
                        game["enemies"].remove(en)
                        game["kills"] += 1
                        burst(particles, en.pos.x, en.pos.y, (255, 60, 60), 15, 4)
                        camera.shake(4)
                    bullets.remove(b)
                    hit = True
                    break
            if hit:
                continue
            if boss and not boss.dead:
                if (boss.pos - b.pos).length() < 24:
                    boss.take_damage(1, particles, camera)
                    bullets.remove(b)
                    if boss.dead:
                        camera.shake(25)
                        burst(particles, boss.pos.x, boss.pos.y, C_BOSS, 50, 7, 80)

        # ── Item collection ───────────────────────────────────────────────────
        for it in game["items"][:]:
            if (it.pos - snake.head).length() < 16:
                if it.type == "ammo":
                    game["ammo"] = min(game["ammo"] + 3, 20)
                    burst(particles, it.pos.x, it.pos.y, (0, 200, 255), 8, 3)
                else:
                    game["keys"] += 1
                    burst(particles, it.pos.x, it.pos.y, (255, 220, 0), 8, 3)
                game["items"].remove(it)

        # ── Unlock exit ───────────────────────────────────────────────────────
        if game["keys"] >= 5:
            game["exit"].open = True

        # ── Boss death → win ──────────────────────────────────────────────────
        if boss and boss.dead and boss.death_timer > 120:
            scene = "win"

        # ── Exit reached → next level ─────────────────────────────────────────
        if game["exit"].open and (game["exit"].pos - snake.head).length() < 16:
            next_level = game["level"] + 1
            _clear_projectiles()
            game = new_level(next_level, boss_level=(next_level >= 3))

        # ── Particle lifecycle ────────────────────────────────────────────────
        for p in particles[:]:
            p.update()
            if p.life <= 0:
                particles.remove(p)

    # ── Draw ──────────────────────────────────────────────────────────────────
    if scene == "menu":
        draw_menu(screen)

    elif scene == "death":
        if game:
            screen.blit(game["maze_surf"],
                        (int(camera.offset.x), int(camera.offset.y)))
        draw_death(screen, death_cause)

    elif scene == "win":
        screen.fill(C_BG)
        draw_win(screen)

    elif scene == "game":
        # Maze
        screen.blit(game["maze_surf"],
                    (int(camera.offset.x), int(camera.offset.y)))

        # World objects
        for it in game["items"]:
            it.draw(screen, camera.offset)
        game["exit"].draw(screen, camera.offset)
        for en in game["enemies"]:
            en.draw(screen, camera.offset)
        if game.get("boss"):
            game["boss"].draw(screen, camera.offset)

        # Projectiles
        for b in bullets:
            b.draw(screen, camera.offset)
        for b in enemy_bullets:
            b.draw(screen, camera.offset)

        # Snake
        snake.draw(screen, camera.offset)

        # Particles
        for p in particles:
            p.draw(screen, camera)

        # HUD
        draw_hud(screen, game)

        # Countdown overlay
        fonts = get_fonts()
        elapsed = (now - game["start"]) / 1000
        if elapsed <= 3 and game["boss_intro"] == 0:
            cnt    = max(0, 3 - int(elapsed))
            label  = str(cnt) if cnt > 0 else "GO!"
            cs     = fonts["big"].render(label, True, C_SNAKE_H)
            screen.blit(cs, (W // 2 - cs.get_width() // 2, H // 2 - 50))

        # Boss intro overlay
        if game["boss_intro"] > 0:
            bi = game["boss_intro"]
            if bi < 60:
                alpha = int(255 - bi * 1.4)
            else:
                alpha = int((180 - bi) * 3 + 50)
            draw_boss_intro(screen, int(abs(alpha)))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
