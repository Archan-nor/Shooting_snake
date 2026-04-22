# Neon Serpent — Project Description

## Overview

**Neon Serpent** is a top-down, mouse-driven maze shooter built entirely with Python and pygame.  
The player controls a glowing snake that navigates a procedurally generated maze across three levels, collecting keys and ammo while fighting off spawning enemies and a multi-phase final boss.

The project demonstrates object-oriented design in a real-time game context: each game entity is a self-contained class responsible for its own state, update logic, and rendering.

---

## Concept

### Gameplay Loop

```
Start Level → Explore Maze → Collect 5 Keys → Unlock EXIT → Next Level
                                   ↓
                         Shoot / Dodge Enemies
                                   ↓
                          Level 3: Defeat Boss → Victory
```

### Core Mechanics

**Snake movement** — The snake head follows the mouse cursor at a constant speed.  
Historical head positions form the body segments.

**Shooting** — Left-click fires a bullet in the cursor's direction; each shot costs one ammo unit.

**Dash** — Right-click teleports the head toward the cursor with a 5-second cooldown, granting 2 seconds of invincibility and wall-phasing.

**Keys & Exit** — Five key items must be collected to unlock the level exit portal.

**Boss (Level 3)** — The *Void Sovereign* has three attack phases:
- **Phase 0** — 8-way spiral bullet spread  
- **Phase 1** — Aimed burst shots, orbiting shield, minion summons  
- **Phase 2** — Dense spiral + slow-tracking laser beam

---

## UML Class Diagram

> See `UML.pdf` in the repository root for the full diagram.

```
┌─────────────┐      uses      ┌──────────────┐
│   main.py   │───────────────▶│    Camera    │
│  (game loop)│                └──────────────┘
└──────┬──────┘
       │ creates / updates
       ▼
┌──────────────┐   fires   ┌────────┐
│    Snake     │──────────▶│ Bullet │
└──────────────┘           └────────┘
       │
       │ interacts
       ▼
┌──────────────┐   fires   ┌────────┐
│    Enemy     │──────────▶│ Bullet │
└──────────────┘           └────────┘

┌──────────────┐   fires   ┌────────┐
│     Boss     │──────────▶│ Bullet │
└─────┬────────┘           └────────┘
      │ spawns
      └──────────▶ Enemy

┌──────────────┐
│     Item     │  (ammo | key)
└──────────────┘

┌──────────────┐
│     Exit     │
└──────────────┘

┌──────────────┐
│   Particle   │  managed by effects.burst()
└──────────────┘
```

### Module Responsibilities

| Module | Responsibility |
|--------|---------------|
| `constants.py` | Screen dimensions, tile grid, colours, shared font cache |
| `renderer.py`  | Stateless draw helpers: glow effects, health bars |
| `effects.py`   | `Camera` (screen-shake) and `Particle` / `burst()` |
| `maze.py`      | Procedural DFS maze generation + pre-rendered surface |
| `bullet.py`    | `Bullet` — wall-collision, lifetime, rendering |
| `snake.py`     | `Snake` — mouse-follow movement, dash, body trail |
| `entities.py`  | `Enemy` and `Boss` — AI, attack patterns, damage |
| `pickups.py`   | `Item` and `Exit` — collection and unlock logic |
| `hud.py`       | All overlay rendering: HUD, menus, death/win screens |
| `level.py`     | `new_level()` factory — assembles the game-state dict |
| `main.py`      | Event loop, scene management, collision resolution |

### Design Patterns Used

**Single Responsibility** — Each class handles one concern (entity, rendering, level data).

**Factory Function** — `new_level()` constructs a complete, consistent game-state dict, making level transitions a single call.

**Camera Shake via Delegation** — The `Camera` object is passed only where needed, avoiding global state.

**Flyweight (fonts)** — `get_fonts()` returns a shared dict; fonts are created once and reused everywhere.
