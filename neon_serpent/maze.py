"""
maze.py
Procedural maze generation (recursive back-tracker) and pre-rendered surface.
"""
import random
import pygame
from .constants import W, H, TILE, COLS, ROWS, C_BG, C_WALL, C_WALL_LIT


def gen_maze() -> list[list[int]]:
    """
    Return a 2-D grid where 1 = wall, 0 = floor.
    Uses a recursive depth-first carver seeded from (1,1).
    Extra random cells are cleared to widen corridors.
    """
    grid = [[1] * COLS for _ in range(ROWS)]

    def carve(x: int, y: int) -> None:
        dirs = [(2, 0), (-2, 0), (0, 2), (0, -2)]
        random.shuffle(dirs)
        for dx, dy in dirs:
            nx, ny = x + dx, y + dy
            if 0 < ny < ROWS - 1 and 0 < nx < COLS - 1 and grid[ny][nx] == 1:
                grid[ny][nx]          = 0
                grid[y + dy // 2][x + dx // 2] = 0
                carve(nx, ny)

    grid[1][1] = 0
    carve(1, 1)

    # Enforce solid border
    for x in range(COLS):
        grid[0][x]      = 1
        grid[ROWS - 1][x] = 1
    for y in range(ROWS):
        grid[y][0]      = 1
        grid[y][COLS - 1] = 1

    # Widen corridors with random clearing
    for _ in range(600):
        grid[random.randint(1, ROWS - 2)][random.randint(1, COLS - 2)] = 0

    # Guarantee open spawn area
    for y in range(1, 6):
        for x in range(1, 6):
            grid[y][x] = 0

    return grid


def build_maze_surface(maze: list[list[int]]) -> pygame.Surface:
    """Pre-render the static maze tiles onto a surface for fast blitting."""
    surf = pygame.Surface((W, H))
    surf.fill(C_BG)
    for y in range(ROWS):
        for x in range(COLS):
            if maze[y][x] == 1:
                color = C_WALL_LIT if (x + y) % 3 == 0 else C_WALL
                pygame.draw.rect(
                    surf, color,
                    (x * TILE + 1, y * TILE + 1, TILE - 2, TILE - 2),
                    border_radius=2,
                )
    return surf
