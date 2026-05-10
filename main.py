"""
main.py
Entry point – main game loop.

Changes vs previous version
----------------------------
- HP/Lives carry over between levels (snake passed into new_level)
- Lives start at 10 (MAX_LIVES in snake.py)
- Boss level: no keys/exit, ammo respawns 5 items every 20 s
- Boss level HUD shows blinking "KILL THE BOSS TO WIN"
- All spawn zones respect HUD bar height
"""
import pygame

from neon_serpent.constants  import W, H, C_BG, C_SNAKE_H, C_RED, C_BOSS, C_GOLD, get_fonts
from neon_serpent.effects    import Camera, burst, spawn_damage
from neon_serpent.bullet     import Bullet
from neon_serpent.level      import new_game, new_level, HUD_ROW
from neon_serpent.hud        import (
    draw_hud, draw_menu, draw_death, draw_win, draw_boss_intro,
    draw_level_transition, draw_phase_transition, draw_tutorial, draw_pause,
    HUD_H, PHASE_ANIM_DURATION,
    START_BTN, TUTORIAL_BTN, ANALYTICS_BTN, QUIT_BTN,
    TUTORIAL_BACK_BTN,
    PAUSE_RESUME_BTN, PAUSE_TUTORIAL_BTN, PAUSE_MENU_BTN, PAUSE_QUIT_BTN,
)
from neon_serpent.pickups    import Item
from neon_serpent.stats      import StatsTracker
from neon_serpent.analytics  import (draw_analytics, BACK_BTN, PREV_BTN, NEXT_BTN,
                                     TL_PREV_BTN, TL_NEXT_BTN, TIMELINE_SCROLL_S)

pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("NEON SERPENT")
clock  = pygame.time.Clock()

# ── Shared state ───────────────────────────────────────────────────────────────
camera          = Camera()
particles: list = []
bullets:   list = []
enemy_bullets:  list = []
missile_anims: list = []
dmg_numbers:  list = []   # floating damage numbers

scene       = "menu"
game        = None
death_time  = 0
death_cause = ""

# ── Stats ──────────────────────────────────────────────────────────────────────
tracker       = StatsTracker()
last_log_time = 0
bullets_fired = 0
bullets_hit   = 0

# ── Analytics ─────────────────────────────────────────────────────────────────
analytics_sessions: dict = {}
analytics_selected_sid: int = 0
timeline_scroll_offset: int = 0
# tutorial return scene: "menu" or "paused"
tutorial_return: str = "menu"

# ── Boss phase transition animation ───────────────────────────────────────────
phase_anim_active   = False
phase_anim_start    = 0
phase_anim_phase    = 1    # which phase we are entering (1 or 2)
phase_anim_boss_pos = (0, 0)

# ── Level transition ───────────────────────────────────────────────────────────
TRANSITION_DURATION = 4000   # ms
transition_start    = 0
transition_level    = 1      # level we are about to enter
transition_cleared: list = []  # levels already cleared
pending_game        = None   # game dict ready to start after transition


# ── Helpers ───────────────────────────────────────────────────────────────────

def _clear_projectiles() -> None:
    bullets.clear()
    enemy_bullets.clear()
    particles.clear()
    missile_anims.clear()
    dmg_numbers.clear()


def _game_over(cause: str) -> None:
    global scene, death_cause, death_time
    tracker.add_event(f"game_over:{cause}")  # encode cause in event string
    tracker.tick(game["snake"], game)        # flush final row with event
    tracker.end_session(save=True)
    scene       = "death"
    death_cause = cause
    death_time  = pygame.time.get_ticks()


def _start_game() -> None:
    global pending_game, transition_start, transition_level, transition_cleared
    global bullets_fired, bullets_hit
    pending_game        = new_game()
    bullets_fired       = 0
    bullets_hit         = 0
    transition_level    = 1
    transition_cleared  = []
    transition_start    = pygame.time.get_ticks()
    _clear_projectiles()
    tracker.start_session()   # one session per playthrough, NOT per level


def _enter_pending_game() -> None:
    """Switch from transition screen into the actual game.

    NOTE: do NOT call tracker.start_session() here — it would discard data
    from previous levels. Session lifetime spans the entire playthrough.
    """
    global game, last_log_time, scene
    game          = pending_game
    now_ms        = pygame.time.get_ticks()
    last_log_time = now_ms
    # Teleport snake back to spawn, clear old body/trail
    game["snake"].reset_position()
    # Preserve total elapsed time by adjusting game["start"] backward by
    # the number of seconds already logged (so per-second tick keeps incrementing)
    if tracker._session_rows:
        last_t = int(tracker._session_rows[-1]["t"])
        game["start"] = now_ms - (last_t + 1) * 1000
    else:
        game["start"] = now_ms
    scene         = "game"


def _next_level(current_game: dict) -> dict:
    """Advance to next level, preserving the snake and ammo."""
    next_lv   = current_game["level"] + 1
    boss_lv   = next_lv >= 3
    return new_level(next_lv, boss_level=boss_lv,
                     snake=current_game["snake"],
                     current_ammo=current_game["ammo"])   # carry ammo


# ── Main loop ──────────────────────────────────────────────────────────────────
running = True
while running:
    screen.fill(C_BG)
    camera.update()
    now   = pygame.time.get_ticks()
    mouse = pygame.mouse.get_pos()

    # ── Hover states ──────────────────────────────────────────────────────────
    start_hover     = START_BTN.collidepoint(mouse)
    tutorial_hover  = TUTORIAL_BTN.collidepoint(mouse)
    analytics_hover = ANALYTICS_BTN.collidepoint(mouse)
    quit_hover      = QUIT_BTN.collidepoint(mouse)
    back_hover      = BACK_BTN.collidepoint(mouse)
    tut_back_hover  = TUTORIAL_BACK_BTN.collidepoint(mouse)
    p_resume_hover  = PAUSE_RESUME_BTN.collidepoint(mouse)
    p_tut_hover     = PAUSE_TUTORIAL_BTN.collidepoint(mouse)
    p_menu_hover    = PAUSE_MENU_BTN.collidepoint(mouse)
    p_quit_hover    = PAUSE_QUIT_BTN.collidepoint(mouse)
    prev_hover      = PREV_BTN.collidepoint(mouse)
    next_hover      = NEXT_BTN.collidepoint(mouse)

    # ── Events ────────────────────────────────────────────────────────────────
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            if scene == "game" or scene == "paused":
                tracker.end_session(save=False)
            running = False

        elif scene == "menu":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if START_BTN.collidepoint(mouse):
                    _start_game()
                    scene = "level_transition"
                elif TUTORIAL_BTN.collidepoint(mouse):
                    tutorial_return = "menu"
                    scene = "tutorial"
                elif ANALYTICS_BTN.collidepoint(mouse) and tracker.has_data():
                    analytics_sessions = tracker.load_sessions()
                    sids_list = sorted(analytics_sessions.keys())
                    analytics_selected_sid = sids_list[-1] if sids_list else 0
                    timeline_scroll_offset = 0
                    scene = "analytics"
                elif QUIT_BTN.collidepoint(mouse):
                    running = False

        elif scene == "analytics":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                scene = "menu"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if BACK_BTN.collidepoint(mouse):
                    scene = "menu"
                elif TL_PREV_BTN.collidepoint(mouse) and TL_PREV_BTN.w > 0:
                    timeline_scroll_offset = max(0, timeline_scroll_offset - TIMELINE_SCROLL_S)
                elif TL_NEXT_BTN.collidepoint(mouse) and TL_NEXT_BTN.w > 0:
                    timeline_scroll_offset += TIMELINE_SCROLL_S
                else:
                    sids_list = sorted(analytics_sessions.keys())
                    if sids_list and analytics_selected_sid in sids_list:
                        cur = sids_list.index(analytics_selected_sid)
                        if PREV_BTN.collidepoint(mouse) and cur > 0:
                            analytics_selected_sid = sids_list[cur - 1]
                            timeline_scroll_offset = 0   # reset on session change
                        elif NEXT_BTN.collidepoint(mouse) and cur < len(sids_list) - 1:
                            analytics_selected_sid = sids_list[cur + 1]
                            timeline_scroll_offset = 0   # reset on session change

        elif scene == "tutorial":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                scene = tutorial_return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if TUTORIAL_BACK_BTN.collidepoint(mouse):
                    scene = tutorial_return

        elif scene == "paused":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                scene = "game"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if PAUSE_RESUME_BTN.collidepoint(mouse):
                    scene = "game"
                elif PAUSE_TUTORIAL_BTN.collidepoint(mouse):
                    tutorial_return = "paused"
                    scene = "tutorial"
                elif PAUSE_MENU_BTN.collidepoint(mouse):
                    tracker.end_session(save=False)   # discard mid-game stats
                    scene = "menu"
                elif PAUSE_QUIT_BTN.collidepoint(mouse):
                    tracker.end_session(save=False)
                    running = False

        elif scene == "level_transition":
            pass   # auto-advance on timer

        elif scene == "win":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                scene = "menu"

        elif scene == "death":
            if now - death_time > 3000:
                scene = "menu"

        elif scene == "game":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                scene = "paused"
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and game["ammo"] > 0:
                    # Lock-on: find nearest enemy/boss within 350px
                    LOCK_RANGE = 350
                    head       = game["snake"].head
                    target     = pygame.Vector2(pygame.mouse.get_pos())
                    best_dist  = LOCK_RANGE
                    for _en in game["enemies"]:
                        _d = (_en.pos - head).length()
                        if _d < best_dist:
                            best_dist = _d
                            target    = pygame.Vector2(_en.pos)
                    _boss = game.get("boss")
                    if _boss and not _boss.dead:
                        _d = (_boss.pos - head).length()
                        if _d < best_dist:
                            target = pygame.Vector2(_boss.pos)
                    bullets.append(Bullet(head, target, speed=10))
                    game["ammo"] -= 1
                    bullets_fired += 1
                    tracker.record_shot()
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

        # ── Per-second stats log ───────────────────────────────────────────────
        if started and now - last_log_time >= 1000:
            tracker.tick(snake, game)
            last_log_time = now

        # ── Boss-level: ammo respawn every 20 s (only after phase 1) ─────────
        if game["boss_level"] and started and game.get("ammo_spawn_active"):
            game["ammo_spawn_timer"] += clock.get_time()
            if game["ammo_spawn_timer"] >= game["ammo_spawn_cd"]:
                game["ammo_spawn_timer"] = 0
                for _ in range(5):
                    game["items"].append(Item(maze, "ammo", hud_row=HUD_ROW))

        # ── Boss spawn_events (phase transitions) ─────────────────────────────
        if boss and boss.spawn_events:
            for ev in boss.spawn_events:
                if ev == "missile4":
                    for _ in range(4):
                        game["items"].append(Item(maze, "missile", hud_row=HUD_ROW))
                elif ev == "ammo5":
                    for _ in range(5):
                        game["items"].append(Item(maze, "ammo", hud_row=HUD_ROW))
                elif ev == "enemies2":
                    from neon_serpent.entities import Enemy as _Enemy
                    for _ in range(2):
                        game["enemies"].append(_Enemy(maze, hud_row=HUD_ROW))
                elif ev == "ammo_spawn_on":
                    game["ammo_spawn_active"] = True
                elif ev.startswith("phase_change_"):
                    entering = int(ev.split("_")[-1])
                    phase_anim_active   = True
                    phase_anim_start    = now
                    phase_anim_phase    = entering
                    phase_anim_boss_pos = (
                        int(boss.pos.x + camera.offset.x),
                        int(boss.pos.y + camera.offset.y),
                    )
                    camera.shake(25)
                    burst(particles, boss.pos.x, boss.pos.y, (200, 0, 255), 60, 8, 80)
            boss.spawn_events.clear()

        # Freeze enemies/bullets during phase animation (player still moves)
        _phase_frozen = phase_anim_active and (now - phase_anim_start < PHASE_ANIM_DURATION)

        if started:
            # Snake always moves
            if snake.move(maze):
                tracker.record_dmg_taken(snake.MAX_HP)
                tracker.add_event("lost_life")
                if snake.lose_life(particles, camera):
                    _game_over("WALL COLLISION")

            # Enemy bullets → take_hit (only when not frozen)
            if not _phase_frozen:
                for b in enemy_bullets[:]:
                    if b.update(maze):
                        enemy_bullets.remove(b)
                        continue
                    if (pygame.Vector2(b.pos) - snake.head).length() < 12:
                        if not snake.is_invincible():
                            tracker.record_dmg_taken(b.damage)
                            if snake.hp - b.damage <= 0:
                                tracker.add_event("lost_life")
                        if snake.take_hit(b.damage, particles, camera):
                            _game_over("OVERWHELMED BY ENEMIES")
                        enemy_bullets.remove(b)
                        continue

            # Boss laser → take_hit
            if boss and not boss.dead:
                if boss.check_laser_hit(snake.head):
                    if not snake.is_invincible():
                        tracker.record_dmg_taken(1)
                        if snake.hp - 1 <= 0:
                            tracker.add_event("lost_life")
                    if snake.take_hit(1, particles, camera):
                        _game_over("INCINERATED BY LASER")

            # Enemy contact → take_hit
            for en in game["enemies"]:
                if (en.pos - snake.head).length() < 16:
                    if not snake.is_invincible():
                        tracker.record_dmg_taken(1)
                        if snake.hp - 1 <= 0:
                            tracker.add_event("lost_life")
                    if snake.take_hit(1, particles, camera):
                        _game_over("CONSUMED BY ENEMIES")

            # Update enemies (frozen during phase animation)
            if not _phase_frozen:
                for en in game["enemies"]:
                    en.update(snake.head, enemy_bullets)

            # Update boss (frozen during phase animation)
            # NOTE: must keep updating when dead so death_timer increments → win
            if boss and not _phase_frozen:
                boss.update(snake.head, enemy_bullets, game["enemies"],
                            maze, particles, camera)

        # ── Player bullets ────────────────────────────────────────────────────
        for b in bullets[:]:
            if b.update(maze):
                bullets.remove(b)
                continue
            hit = False
            for en in game["enemies"][:]:
                if (en.pos - b.pos).length() < 14:
                    en.hit(particles)
                    spawn_damage(dmg_numbers, en.pos.x, en.pos.y, 1)
                    tracker.record_hit(damage=1)
                    if en.hp <= 0:
                        game["enemies"].remove(en)
                        game["kills"] += 1
                        bullets_hit += 1
                        tracker.record_kill()
                        burst(particles, en.pos.x, en.pos.y, (255, 60, 60), 15, 4)
                        camera.shake(4)
                    bullets.remove(b)
                    hit = True
                    break
            if hit:
                continue
            if boss and not boss.dead:
                if (boss.pos - b.pos).length() < 24:
                    boss.take_damage(1, particles, camera, player_head=snake.head)
                    spawn_damage(dmg_numbers, boss.pos.x, boss.pos.y - 20, 1)
                    tracker.record_hit(damage=1)
                    bullets_hit += 1
                    bullets.remove(b)
                    if boss.dead:
                        camera.shake(25)
                        burst(particles, boss.pos.x, boss.pos.y, C_BOSS, 50, 7, 80)

        # ── Items ─────────────────────────────────────────────────────────────
        for it in game["items"][:]:
            if (it.pos - snake.head).length() < 16:
                if it.type == "ammo":
                    game["ammo"] = min(game["ammo"] + 3, 20)
                    tracker.add_event("ammo_collected")
                    burst(particles, it.pos.x, it.pos.y, (0, 200, 255), 8, 3)
                elif it.type == "key":
                    game["keys"] += 1
                    tracker.add_event("key_collected")
                    burst(particles, it.pos.x, it.pos.y, (255, 220, 0), 8, 3)
                elif it.type == "missile" and boss and not boss.dead:
                    burst(particles, it.pos.x, it.pos.y, (255, 120, 0), 10, 3, 20)
                    missile_anims.append({
                        "pos":  pygame.Vector2(it.pos),
                        "boss": boss,
                        "done": False,
                    })
                game["items"].remove(it)

        # Normal level: unlock exit when 5 keys collected
        if not game["boss_level"] and game["keys"] >= 5:
            if game["exit"]:
                game["exit"].open = True

        # ── Boss dead → WIN ────────────────────────────────────────────────────
        if boss and boss.dead and boss.death_timer > 120:
            tracker.add_event("victory")
            tracker.tick(snake, game)        # flush final row with event
            tracker.end_session(save=True)
            scene = "win"


        # ── Exit reached → level transition screen ──────────────────────────
        if (not game["boss_level"]
                and game["exit"] and game["exit"].open
                and (game["exit"].pos - snake.head).length() < 16):
            _clear_projectiles()
            next_lv = game["level"] + 1
            transition_cleared.append(game["level"])
            transition_level   = next_lv
            transition_start   = pygame.time.get_ticks()
            pending_game       = _next_level(game)
            scene              = "level_transition"
        # ── Missile animations ────────────────────────────────────────────────
        for ma in missile_anims[:]:
            if ma["done"]:
                missile_anims.remove(ma)
                continue
            b = ma["boss"]
            if b.dead:
                missile_anims.remove(ma)
                continue
            d = b.pos - ma["pos"]
            if d.length() < 12:
                burst(particles, ma["pos"].x, ma["pos"].y, (255, 120, 0), 30, 6, 50)
                burst(particles, ma["pos"].x, ma["pos"].y, (255, 255, 100), 15, 4, 35)
                camera.shake(12)
                b.take_damage(8, particles, camera, player_head=snake.head)
                spawn_damage(dmg_numbers, b.pos.x, b.pos.y - 30, 8)
                # NOTE: missile is not a shot — don't count toward accuracy.
                # Damage dealt is recorded separately via dmg_dealt below.
                tracker._dmg_dealt += 8   # raw damage, no hit/shot increment
                tracker.add_event("missile_hit")
                if b.dead:
                    camera.shake(25)
                    burst(particles, b.pos.x, b.pos.y, C_BOSS, 50, 7, 80)
                ma["done"] = True
            else:
                ma["pos"] += d.normalize() * 8

        # ── Damage numbers ────────────────────────────────────────────────────
        for dn in dmg_numbers[:]:
            dn.update()
            if dn.life <= 0:
                dmg_numbers.remove(dn)

        # ── Particles ─────────────────────────────────────────────────────────
        for p in particles[:]:
            p.update()
            if p.life <= 0:
                particles.remove(p)

    # ── Draw ──────────────────────────────────────────────────────────────────
    # ── Boss phase animation expiry ──────────────────────────────────────────
    if phase_anim_active and now - phase_anim_start >= PHASE_ANIM_DURATION:
        phase_anim_active = False

    # ── Level transition auto-advance ────────────────────────────────────────
    if scene == "level_transition":
        if pygame.time.get_ticks() - transition_start >= TRANSITION_DURATION:
            _enter_pending_game()

    # ── Draw ─────────────────────────────────────────────────────────────────
    if scene == "level_transition":
        elapsed_ms = pygame.time.get_ticks() - transition_start
        draw_level_transition(
            screen,
            entering_level = transition_level,
            cleared_levels = transition_cleared,
            snake          = pending_game["snake"] if transition_level > 1 else None,
            current_ammo   = pending_game["ammo"],
            elapsed_ms     = elapsed_ms,
            duration_ms    = TRANSITION_DURATION,
        )

    elif scene == "menu":
        draw_menu(screen,
                  has_data        = tracker.has_data(),
                  start_hover     = start_hover,
                  tutorial_hover  = tutorial_hover,
                  analytics_hover = analytics_hover,
                  quit_hover      = quit_hover)

    elif scene == "analytics":
        draw_analytics(
            screen,
            sessions               = analytics_sessions,
            selected_sid           = analytics_selected_sid,
            btn_back_hover         = back_hover,
            btn_prev_hover         = prev_hover,
            btn_next_hover         = next_hover,
            timeline_scroll_offset = timeline_scroll_offset,
        )

    elif scene == "death":
        if game:
            screen.blit(game["maze_surf"],
                        (int(camera.offset.x), int(camera.offset.y)))
        draw_death(screen, death_cause)

    elif scene == "win":
        screen.fill(C_BG)
        draw_win(screen)

    elif scene == "tutorial":
        draw_tutorial(screen, back_hover=tut_back_hover)

    elif scene == "paused":
        # Render frozen game state behind pause overlay
        if game:
            screen.blit(game["maze_surf"],
                        (int(camera.offset.x), int(camera.offset.y)))
            for it in game["items"]:
                it.draw(screen, camera.offset)
            if game.get("exit"):
                game["exit"].draw(screen, camera.offset)
            for en in game["enemies"]:
                en.draw(screen, camera.offset)
            if game.get("boss"):
                game["boss"].draw(screen, camera.offset)
            for b in bullets:
                b.draw(screen, camera.offset)
            for b in enemy_bullets:
                b.draw(screen, camera.offset)
            game["snake"].draw(screen, camera.offset)
            draw_hud(screen, game)
        draw_pause(
            screen,
            resume_hover   = p_resume_hover,
            tutorial_hover = p_tut_hover,
            menu_hover     = p_menu_hover,
            quit_hover     = p_quit_hover,
        )

    elif scene == "game":
        snake = game["snake"]   # ensure local ref exists for draw
        screen.blit(game["maze_surf"],
                    (int(camera.offset.x), int(camera.offset.y)))

        for it in game["items"]:
            it.draw(screen, camera.offset)

        # Exit only exists on normal levels
        if game["exit"]:
            game["exit"].draw(screen, camera.offset)

        for en in game["enemies"]:
            en.draw(screen, camera.offset)
        if game.get("boss"):
            game["boss"].draw(screen, camera.offset)

        for b in bullets:
            b.draw(screen, camera.offset)
        for b in enemy_bullets:
            b.draw(screen, camera.offset)

        snake.draw(screen, camera.offset)

        # Draw missile animations
        for ma in missile_anims:
            if not ma["done"]:
                mp = (int(ma["pos"].x + camera.offset.x),
                      int(ma["pos"].y + camera.offset.y))
                pygame.draw.circle(screen, (255, 160, 0), mp, 6)
                pygame.draw.circle(screen, (255, 220, 100), mp, 3)
                burst(particles, ma["pos"].x, ma["pos"].y, (255, 100, 0), 2, 1, 8)

        for p in particles:
            p.draw(screen, camera)

        # Draw damage numbers
        for dn in dmg_numbers:
            dn.draw(screen, camera, get_fonts())

        draw_hud(screen, game)

        # Boss phase transition animation overlay
        if phase_anim_active:
            elapsed_anim = now - phase_anim_start
            draw_phase_transition(
                screen,
                boss_pos       = phase_anim_boss_pos,
                entering_phase = phase_anim_phase,
                elapsed_ms     = elapsed_anim,
            )

        # Countdown
        fonts = get_fonts()
        elapsed_s = (now - game["start"]) / 1000
        if elapsed_s <= 3 and game["boss_intro"] == 0:
            cnt   = max(0, 3 - int(elapsed_s))
            label = str(cnt) if cnt > 0 else "GO!"
            # Dim overlay — fade out on "GO!"
            dim_alpha = 160 if cnt > 0 else 60
            dim = pygame.Surface((W, H), pygame.SRCALPHA)
            dim.fill((0, 0, 0, dim_alpha))
            screen.blit(dim, (0, 0))
            # Number / GO!
            col = C_SNAKE_H if cnt > 0 else C_GOLD
            cs  = fonts["big"].render(label, True, col)
            screen.blit(cs, (W // 2 - cs.get_width() // 2, H // 2 - 50))

        if game["boss_intro"] > 0:
            bi    = game["boss_intro"]
            alpha = int(255 - bi * 1.4) if bi < 60 else int((180 - bi) * 3 + 50)
            draw_boss_intro(screen, int(abs(alpha)))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()