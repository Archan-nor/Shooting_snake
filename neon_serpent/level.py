"""
level.py
Level factory and game-state management.

Rules
-----
- Snake HP/Lives carry over between levels (snake object is passed in).
- Boss level (level >= 3): no keys, no exit door, ammo spawns every 20 s.
- Normal levels: keys + exit as before.
- Spawn zones for enemies/items start below HUD (y >= HUD_ROW).
"""
import pygame
from .maze     import gen_maze, build_maze_surface
from .snake    import Snake
from .entities import Enemy, Boss
from .pickups  import Item, Exit
from .hud      import HUD_H
from .constants import TILE

# First tile row that is fully below the HUD bar
HUD_ROW = HUD_H // TILE + 1   # e.g. HUD_H=44, TILE=26 → row 2+1 = 3


def new_level(level: int, boss_level: bool = False,
              snake: Snake | None = None,
              current_ammo: int | None = None) -> dict:
    """
    Build a fresh game-state dict for *level*.

    Parameters
    ----------
    snake : existing Snake to carry over (HP/Lives preserved).
            If None, a new Snake is created (first game only).
    """
    maze      = gen_maze()
    maze_surf = build_maze_surface(maze)
    n_enemies = 5 + level * 3
    n_ammo    = 8 + level

    # Reuse or create snake
    if snake is None:
        snake = Snake()

    if boss_level:
        # Boss level: start with missile4 + ammo5 (rest spawned by boss events)
        items    = (
            [Item(maze, "missile", hud_row=HUD_ROW) for _ in range(4)] +
            [Item(maze, "ammo",    hud_row=HUD_ROW) for _ in range(5)]
        )
        exit_obj = None
    else:
        items = (
            [Item(maze, "ammo", hud_row=HUD_ROW) for _ in range(n_ammo)] +
            [Item(maze, "key",  hud_row=HUD_ROW) for _ in range(5)]
        )
        exit_obj = Exit(maze, hud_row=HUD_ROW)

    return {
        "snake":            snake,
        "maze":             maze,
        "maze_surf":        maze_surf,
        "enemies":          [] if boss_level else [Enemy(maze, hud_row=HUD_ROW) for _ in range(n_enemies)],
        "boss":             Boss(maze) if boss_level else None,
        "boss_level":       boss_level,
        "items":            items,
        "exit":             exit_obj,          # None on boss level
        "ammo":             current_ammo if current_ammo is not None else 5,
        "keys":             0,
        "start":            pygame.time.get_ticks(),
        "level":            level,
        "kills":            0,
        "boss_intro":       180 if boss_level else 0,
        # Boss-level ammo respawn: enabled when boss hits phase 1
        "ammo_spawn_timer":  0,
        "ammo_spawn_cd":     20_000,
        "ammo_spawn_active": False,            # enabled by boss phase 1
    }


def new_game() -> dict:
    """Start from level 1 with a brand-new snake."""
    return new_level(1, snake=None)
