# Project Description

## 1. Project Overview

- **Project Name:** Neon Serpent
- **Brief Description:**
  Neon Serpent is a top-down, mouse-driven maze shooter built entirely with
  Python and pygame. The player controls a glowing snake that navigates three
  procedurally generated maze levels, collecting keys and ammo while fighting
  off spawning enemies. The final stage pits the player against a three-phase
  boss called the *Void Sovereign*, which changes attack patterns as its HP
  drops. Every gameplay action — shots fired, hits landed, damage dealt and
  taken, position, lives, level — is recorded once per second to a CSV file
  and surfaced through an in-game analytics dashboard so players can review
  and learn from their own runs.

- **Problem Statement:**
  Most simple action games show only a final score on the death screen. Players
  rarely get to see *how* they performed across a run — when they took the
  most damage, where they spent their time, whether they actually aim or just
  spam shots. Neon Serpent addresses this by recording per-second telemetry
  and visualising it in four complementary graphs, turning each session into a
  short post-game review.

- **Target Users:**
  Casual action-game players who enjoy short runs (2–5 minutes) and want a
  quick way to see where they can improve.

- **Key Features:**
  - Mouse-driven snake movement with a click-to-shoot, right-click-to-dash combat loop
  - Lock-on shooting that auto-aims at the nearest enemy or boss within 350 px
  - Three levels with a procedurally generated maze and a 5-key unlock gate
  - Three-phase final boss with knockback, summon waves, and a charged rifle attack
  - Missile pickups that fire automatically toward the boss for heavy damage
  - Per-life HP system (10 lives × 3 HP each, total 33 HP), with 5-second
    invincibility and wall-phase after losing a life
  - Pause menu (ESC) with resume / tutorial / quit-to-menu / quit-game options
  - Per-second statistics tracking, persisted to `game_stats.csv`
  - Analytics dashboard with 5 KPI cards, 1 timeline, and 3 small graphs
    covering 4 distinct chart types (line, bar, scatter, stacked area)
  - Up to 5 most recent sessions kept on disk; older sessions trimmed automatically

- **Screenshots:** see [`screenshots/gameplay/`](screenshots/gameplay/) for
  in-game shots and [`screenshots/visualization/`](screenshots/visualization/)
  for the analytics dashboard.

- **Proposal:** see [`proposal.pdf`](proposal.pdf).

- **YouTube Presentation:** 

---

## 2. Concept

### 2.1 Background

The project started from a desire to combine two things we usually see
separately: a fast, reflex-driven arcade game, and a clean dashboard of
gameplay data. Most games either don't track meaningful telemetry, or hide it
behind external tools. We wanted a self-contained game where the data layer is
a first-class part of the experience — built into the same window, drawn with
the same visual language, and surfaced *immediately* after every run.

The maze-shooter format was chosen because it produces clearly distinguishable
behaviours (movement patterns, shooting cadence, damage exchanges) that map
naturally onto different chart types. A multi-phase boss adds variation across
a run so the timeline is never flat.

### 2.2 Objectives

- Build a complete, polished pygame action game with three levels and a multi-phase boss.
- Record per-second player telemetry that captures *behaviour*, not just final score.
- Surface that telemetry through an in-game analytics screen using at least
  four distinct chart types covering different categories (time-series,
  distribution, relation, proportion).
- Keep the entire stack — game, data layer, and visualisation — in pure Python
  with pygame as the only runtime dependency.

---

## 3. UML Class Diagram

The full class diagram is provided as [`UML.pdf`](UML.pdf) in the repository
root. A high-level summary is shown below; see the PDF for attributes,
methods, and relationship arrows.

```
                        ┌──────────────┐
                        │    main.py   │   (game loop / scene FSM)
                        └──────┬───────┘
                               │ owns / drives
        ┌──────────────────────┼───────────────────────────┐
        ▼                      ▼                           ▼
   ┌─────────┐          ┌──────────────┐           ┌──────────────┐
   │  Snake  │          │  StatsTracker│           │    Camera    │
   └────┬────┘          └──────────────┘           └──────────────┘
        │ fires
        ▼
   ┌─────────┐                                     ┌──────────────┐
   │ Bullet  │◀────fires─── Enemy / Boss           │  Particle    │
   └─────────┘                                     │  DamageNumber│
                                                   └──────────────┘
   ┌─────────┐  collected by Snake  ┌─────────┐
   │  Item   │─────────────────────▶│  Snake  │
   └─────────┘  (ammo / key /        └─────────┘
                missile)

   ┌─────────┐  unlocks → next level
   │  Exit   │
   └─────────┘
```

**Submission Requirement:** the diagram is attached as `UML.pdf` per the
project guidelines.

---

## 4. Object-Oriented Programming Implementation

The codebase is split into a thin `main.py` entry point and a `neon_serpent/`
package containing all gameplay classes and helper modules.

| Class            | File           | Role |
|------------------|----------------|------|
| **`Snake`**      | `snake.py`     | Player character. Handles mouse-follow movement, body trail, lives/HP, dash mechanic, and immortality window after losing a life. |
| **`Bullet`**     | `bullet.py`    | Projectile fired by the player or by enemies/boss. Has `pierce_wall` flag for the boss's rifle attack. |
| **`Enemy`**      | `entities.py`  | Standard enemy with simple chase / flee / shoot AI. Spawns at random walkable tiles below the HUD. |
| **`Boss`**       | `entities.py`  | The Void Sovereign. State machine for three phases (HP 120→81, 80→41, 40→0), each with its own attack pattern, plus knockback, rifle aim/fire cycle, and summon waves. |
| **`Item`**       | `pickups.py`   | Ammo / key / missile pickups. Missile triggers an animation and auto-fires at the boss. |
| **`Exit`**       | `pickups.py`   | Level-exit portal — locked until 5 keys are collected (normal levels only). |
| **`Camera`**     | `effects.py`   | Screen-space offset with shake support, applied during rendering. |
| **`Particle`**   | `effects.py`   | Short-lived visual effect spawned by `burst()`. |
| **`DamageNumber`** | `effects.py` | Floating "-N" label that rises and fades whenever an enemy or the boss takes a hit. |
| **`StatsTracker`** | `stats.py`   | Per-second telemetry recorder. Accumulates deltas (shots / hits / kills / dmg) within each tick, flushes a row, and persists the latest 5 sessions to `game_stats.csv`. |

The remaining helper modules contain stateless functions rather than classes:

| Module          | Responsibility |
|-----------------|---------------|
| `constants.py`  | Screen size, tile grid, palette, font cache. |
| `renderer.py`   | Stateless draw helpers (glow circle, glow rect, health bar). |
| `maze.py`       | Recursive-DFS maze generation + pre-rendered surface, with the top rows reserved for the HUD. |
| `hud.py`        | All overlay rendering: in-game HUD, menu / tutorial / pause / death / win / boss-intro / level-transition / phase-transition screens. |
| `level.py`      | `new_level()` factory that assembles a complete game-state dict (maze, items, enemies, exit, snake) and `new_game()` for the first level. |
| `analytics.py`  | The data dashboard: KPI cards, performance timeline, and the three small graphs (A: shooting activity, B: movement heatmap, C: damage balance). |

### Design patterns used

- **Single Responsibility** — each class owns one concern: movement (`Snake`),
  AI (`Boss`), data (`StatsTracker`), screen-shake (`Camera`), etc.
- **Factory function** — `new_level()` returns a fully-initialised
  game-state dict, so a level transition is a single call.
- **State machine** — `Boss.phase` is an integer property; its setter triggers
  spawn events that `main.py` reads each frame and acts on.
- **Event queue** — `Boss.spawn_events` is a list of strings (e.g.
  `"missile4"`, `"phase_change_1"`); the main loop drains and reacts to it,
  keeping `Boss` free of dependencies on level / item code.
- **Flyweight (fonts)** — `get_fonts()` returns a shared dict; every renderer
  uses the same font objects instead of recreating them.

---

## 5. Statistical Data

### 5.1 Data Recording Method

Telemetry is captured by the `StatsTracker` class (`stats.py`). The flow is:

1. **Session start** — `tracker.start_session()` is called once when the player
   selects START GAME from the menu. A new `session_id` is assigned (one
   higher than the maximum already on disk).
2. **Per-action recording** — during gameplay, the main loop calls small
   methods on the tracker as events occur:
   - `record_shot()` when the player fires a bullet
   - `record_hit(damage)` when a player bullet hits an enemy or the boss
   - `record_kill()` when an enemy is killed
   - `record_dmg_taken(damage)` when the snake is hit
   - `add_event(name)` for one-off markers (`lost_life`, `key_collected`,
     `ammo_collected`, `missile_hit`, `victory`, `game_over:CAUSE`)
3. **Tick (1 Hz)** — once per second, `tracker.tick(snake, game)` flushes a
   row containing the accumulated counters plus a snapshot of the snake's
   state, then resets the counters. The recorded fields are listed in §5.2.
4. **Session end** — when the player dies or wins, `tracker.end_session(save=True)`
   appends the rows to `game_stats.csv`, keeping only the 5 most recent
   sessions. If the player quits mid-game (pause-menu Quit, window close), the
   tracker is called with `save=False` and the rows are discarded — incomplete
   runs do not contaminate the statistics.

### 5.2 Data Features

Each row of `game_stats.csv` contains the following 13 columns:

| Column        | Type | Description |
|---------------|------|-------------|
| `session_id`  | int  | 1-up id, distinguishes runs |
| `t`           | int  | Seconds since the run started |
| `level`       | int  | Current level (1, 2, or 3) |
| `hp`          | int  | Current HP within the active life (0–3) |
| `lives`       | int  | Lives remaining (0–10) |
| `pos_x`       | int  | Snake head X position in world coords (0–1400) |
| `pos_y`       | int  | Snake head Y position in world coords (0–800) |
| `shots`       | int  | Bullets fired during this second |
| `hits`        | int  | Bullets that hit a target during this second |
| `dmg_dealt`   | int  | Damage dealt to enemies / boss this second |
| `dmg_taken`   | int  | Damage received this second |
| `kills`       | int  | Enemies killed this second |
| `event`       | str  | Optional marker (`lost_life` / `key_collected` / `ammo_collected` / `missile_hit` / `victory` / `game_over:CAUSE`) |

All numeric counters are **per-second deltas**, not cumulative. This makes
distribution-style charts (e.g. histograms of shooting activity) trivial to
compute, and cumulative views are still easy to derive when needed by summing.

The dashboard uses these features to compute:

- **5 KPI cards** — outcome (with death cause when LOST), survived time,
  accuracy (clamped to 100 %), kills, deaths.
- **Performance Timeline** — HP/Lives line on the left axis, cumulative kills
  on the right axis, with level bands and event markers.
- **Graph A: Shooting Activity** — bar graph of total shots per 20-second window.
- **Graph B: Movement Heatmap** — scatter of all `(pos_x, pos_y)` samples,
  showing where the player spent time.
- **Graph C: Damage Balance** — stacked area: damage taken on the bottom,
  damage dealt stacked above, aggregated into 10-second windows.

This combination covers four distinct chart categories — time-series, bar
distribution, relation/scatter, and proportion (stacked area) — as required
by the rubric.

---

## 6. Changed Proposed Features

---

## 7. External Sources

- **pygame 2.6.1** — game runtime. <https://www.pygame.org/>
  License: LGPL.
- All code, art, sound, and game design in this repository are original work
  by the project author. No third-party assets are used.
