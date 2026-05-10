# Neon Serpent

A neon-themed maze shooter built with **pygame**, featuring a multi-phase boss
and a built-in analytics dashboard that visualises every run.

## Project Description

- **Project by:** *(your name here)*
- **Game Genre:** Action, Arcade, Top-down Shooter

You play as a glowing serpent that snakes through three procedurally generated
mazes. Collect keys to unlock the level exit, manage ammo and lives, and
finally take down the three-phase **Void Sovereign** boss. Every run is
recorded second-by-second and visualised in an in-game data dashboard, so you
can review your accuracy, movement, and damage curve after each session.

For the full project description (concept, OOP design, statistical data
features, UML), see [`DESCRIPTION.md`](DESCRIPTION.md).

---

## Installation

### 1. Clone this project

```sh
git clone https://github.com/<username>/neon-serpent.git
cd neon-serpent
```

### 2. Create and activate a Python virtual environment

**Windows (cmd / PowerShell):**

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**macOS / Linux:**

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> Python 3.11 or newer is required (the code uses `int | None` style type hints).

---

## Running Guide

After activating the virtual environment, run from the project root:

**Windows:**

```bat
python main.py
```

**macOS / Linux:**

```sh
python3 main.py
```

The window opens at **1400 × 800** pixels. The game runs at 60 FPS.

---

## Tutorial / Usage

### Main menu

When the game starts, four buttons appear:

| Button | Action |
|--------|--------|
| **START GAME**    | Begin a new run from level 1 |
| **TUTORIAL**      | Show controls / combat / objective help |
| **DATA ANALYTICS**| Open the analytics dashboard (greyed out until you've played at least one run) |
| **QUIT GAME**     | Close the window |

### Controls (in-game)

| Input | Action |
|-------|--------|
| Mouse movement | Steer the snake — the head follows the cursor |
| **Left click** | Shoot. Auto-locks onto the nearest enemy or boss within 350 px; otherwise fires toward the cursor. Costs 1 ammo. |
| **Right click**| **DASH** — teleport toward the cursor. 5-second cooldown, grants 2 seconds of invincibility and lets you phase through walls. |
| **ESC**        | Pause the game (opens a menu with Resume / Tutorial / Quit-to-menu / Quit-game) |

> Quitting from the pause menu **does not save** the current session's stats.
> Stats are saved only when the run ends in death or victory.

### Objective

1. **Levels 1 and 2** — explore the maze, pick up **5 keys** (yellow `K`),
   then walk into the **EXIT** portal once it unlocks.
2. **Level 3 (Boss)** — there is no exit. Defeat the **Void Sovereign** to win.

### Pickups

| Pickup        | Visual     | Effect |
|---------------|------------|--------|
| Ammo          | Cyan `A`   | +3 ammo (cap 20) |
| Key           | Yellow `K` | Counts toward the 5 keys needed to unlock the exit |
| Missile       | Orange `M` (boss level only) | Auto-fires at the boss for 8 damage |

### Lives & HP

- You start with **10 lives**, each with **3 HP** (33 HP total).
- Losing all 3 HP from a life costs 1 life and grants **5 seconds** of
  invincibility + wall-phase to recover.
- Hitting a wall while not dashing instantly costs 1 full life.

### Boss phases

The Void Sovereign cycles through three phases as its HP drops:

| Phase | HP range | Behaviour |
|-------|----------|-----------|
| **0 — Awakening** | 120–81 | 8-way spiral bullet pattern |
| **1 — Enraged**   | 80–41  | Aimed 5-shot bursts, 6 orbiting orbs, summons 2 enemies on entry and another 2 every 5 s if there are fewer than 4 alive |
| **2 — Final Form**| 40–0   | Dense 12-way spiral + a charged rifle attack every 13 s (3 s aim with a red dashed line, then a wall-piercing high-speed shot) |

The phase transitions trigger a 2-second cinematic; enemies and the boss
freeze during it so you can reposition.

### Analytics dashboard

After at least one run, the **DATA ANALYTICS** button on the main menu opens
the dashboard. Use the `<` / `>` buttons to switch between the 5 most recent
sessions. Each session view shows:

- **5 KPI cards** — Outcome (with death cause), Survived, Accuracy, Kills, Deaths
- **Performance Timeline** — HP / Lives over time + cumulative kills, with
  level bands and event markers
- **Graph A** — Shooting Activity (shots per 20-second window)
- **Graph B** — Movement Heatmap (where the snake spent time)
- **Graph C** — Damage Balance (stacked area: damage taken vs damage dealt)

---

## Game Features

- Three procedurally generated maze levels with a 5-key unlock gate
- Three-phase boss fight with knockback, summon waves, and a charged rifle
- Lock-on shooting that auto-aims at the nearest target
- 10-life × 3-HP system with 5-second post-death invincibility
- Mouse-driven movement, click-to-shoot, right-click-to-dash combat loop
- Pause menu with full tutorial reference
- Per-second telemetry persisted to `game_stats.csv` (latest 5 runs)
- In-game analytics dashboard with 4 distinct chart types

---

## Known Bugs

- On rare occasions a maze wall tile may render with a one-pixel seam at the
  edge of the screen — purely visual, does not affect collision.

---

## Unfinished Works

All planned features for the 10-May submission are complete.

---

## External Sources

- **pygame 2.6.1** — game framework, <https://www.pygame.org/>
- All other code, art, and game design in this project are original work by
  the project author.
