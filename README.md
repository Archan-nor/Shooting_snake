# Neon Serpent

A neon-themed maze shooter built with **pygame**.  
Navigate a glowing snake through procedurally generated mazes, collect keys, blast enemies, and defeat the three-phase **Void Sovereign** boss.

---

## Requirements

| Dependency | Version |
|------------|---------|
| Python     | 3.11+   |
| pygame     | 2.6.1   |

---

## Installation

### 1 · Clone the repository
```bash
git clone https://github.com/<your-username>/neon-serpent.git
cd neon-serpent
```

### 2 · Create and activate a virtual environment
```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3 · Install dependencies
```bash
pip install -r requirements.txt
```

---

## Running the game

```bash
python main.py
```

The game window opens at **1400 × 800** pixels.  
Press **ENTER** on the main menu to begin.

---

## Controls

| Input | Action |
|-------|--------|
| Mouse movement | Steer the snake |
| Left click | Shoot (costs 1 ammo) |
| Right click | **DASH** — teleport toward cursor (5 s cooldown, grants 2 s invincibility + wall-phase) |

---

## Objective

1. Explore the maze and collect **5 keys** (yellow `K` pickups).
2. Grab **ammo** (cyan `A` pickups) to keep shooting.
3. Reach the **EXIT** portal once it unlocks.
4. Survive until **Level 3**, where the **Void Sovereign** boss awaits.

---

## Project Structure

```
neon-serpent/
├── main.py                  # Entry point / main loop
├── requirements.txt
├── README.md
├── DESCRIPTION.md
├── LICENSE
├── neon_serpent/            # Game package
│   ├── __init__.py
│   ├── constants.py         # Screen size, colours, fonts
│   ├── renderer.py          # Stateless draw helpers
│   ├── effects.py           # Camera shake, particles
│   ├── maze.py              # Procedural maze generation
│   ├── bullet.py            # Bullet projectile
│   ├── snake.py             # Player snake
│   ├── entities.py          # Enemy and Boss classes
│   ├── pickups.py           # Item and Exit classes
│   ├── hud.py               # HUD + all overlay screens
│   └── level.py             # Level factory
└── screenshots/
    ├── gameplay/
    └── visualization/
        └── VISUALIZATION.md
```
# Shooting_snake
