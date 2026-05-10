"""
constants.py
All game-wide constants: screen size, tile grid, colours, and fonts.
Centralising these here means a single import covers every module.
"""
import pygame

# ── Screen & Grid ────────────────────────────────────────────────────────────
W, H     = 1400, 800
TILE     = 26
COLS     = W // TILE
ROWS     = H // TILE

# HUD bar height — walls are enforced for rows 0..PLAY_ROW_MIN-1
HUD_H_CONST   = 44                      # must match hud.HUD_H
PLAY_ROW_MIN  = HUD_H_CONST // TILE + 1 # first fully-playable tile row

# ── Colours ──────────────────────────────────────────────────────────────────
C_BG         = (5,   5,  15)
C_WALL       = (20,  20,  50)
C_WALL_LIT   = (35,  35,  80)
C_SNAKE_H    = (0,  255, 120)
C_SNAKE_B    = (0,  180,  80)
C_SNAKE_I    = (80, 200, 255)
C_ENEMY      = (255,  60,  60)
C_BOSS       = (200,   0, 255)
C_AMMO       = (0,  200, 255)
C_KEY        = (255, 220,   0)
C_EXIT       = (0,  255, 100)
C_BULLET     = (255, 240,  80)
C_BOSS_PROJ  = (255,  80, 255)
C_HUD_BG     = (10,  10,  30)
C_HUD_BORDER = (0,  200, 255)
C_RED        = (255,  50,  50)
C_GOLD       = (255, 215,   0)
C_WHITE      = (220, 220, 255)
C_DIM        = (80,  80, 100)

# ── Fonts (initialised lazily so pygame.init() need not run at import time) ──
_fonts: dict = {}

def get_fonts() -> dict:
    """Return the shared font dict, initialising on first call."""
    if not _fonts:
        _fonts["mono"] = pygame.font.SysFont("consolas", 20)
        _fonts["big"]  = pygame.font.SysFont("consolas", 72, bold=True)
        _fonts["med"]  = pygame.font.SysFont("consolas", 36, bold=True)
        _fonts["sm"]   = pygame.font.SysFont("consolas", 16)
    return _fonts
