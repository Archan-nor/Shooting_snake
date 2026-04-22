"""
level.py
Level factory and game-state management.
"""
import pygame
from .maze     import gen_maze, build_maze_surface
from .snake    import Snake
from .entities import Enemy, Boss
from .pickups  import Item, Exit


def new_level(level: int, boss_level: bool = False) -> dict:
    """
    Build and return a fresh game-state dict for *level*.

    The dict is the single source-of-truth passed around by the main loop.
    """
    maze      = gen_maze()
    maze_surf = build_maze_surface(maze)
    n_enemies = 5 + level * 3
    n_ammo    = 8 + level

    return {
        "snake":      Snake(),
        "maze":       maze,
        "maze_surf":  maze_surf,
        "enemies":    [Enemy(maze) for _ in range(n_enemies)],
        "boss":       Boss(maze) if boss_level else None,
        "boss_level": boss_level,
        "items":      (
            [Item(maze, "ammo") for _ in range(n_ammo)] +
            [Item(maze, "key")  for _ in range(5)]
        ),
        "exit":       Exit(maze),
        "ammo":       5,
        "keys":       0,
        "start":      pygame.time.get_ticks(),
        "level":      level,
        "kills":      0,
        "boss_intro": 180 if boss_level else 0,
    }


def new_game() -> dict:
    """Convenience wrapper – start from level 1."""
    return new_level(1)
