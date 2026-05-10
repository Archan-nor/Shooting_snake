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
  - https://youtu.be/FcMCyZwiP50

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

The final game diverges from the original proposal in several places.
This section walks through the changes by section so a reviewer can compare
them directly against the proposal document.

### 6.0 Project name

The proposal used the working title **"Shooting Snake — Snake Survival:
Action-Based Data Analysis Game"**, which was descriptive but plain.
The final game is titled **"Neon Serpent"** to better fit its visual identity
(neon-glow palette, dark maze background, cinematic boss reveals) and to give
the project a shorter, more memorable name suitable for the title screen,
GitHub repository, and presentation video.

### 6.1 Game concept and structure

The proposal described **a single 2-minute survival round** in an open arena
where the player accumulates score, with a "score penalty instead of full
reset" on death.

The final game replaces this with a **three-level structure with a defined
ending**:

- Levels 1 and 2 are procedurally generated mazes. The player must collect
  **5 keys** to unlock the **EXIT** portal, then enter it to advance.
- Level 3 has no keys or exit — it is a boss arena. The player must defeat
  the multi-phase **Void Sovereign** to win the run.
- A run ends in **WIN** (boss defeated) or **LOST** (all 10 lives gone).
  There is no fixed time limit and no continuous score — instead, every
  meaningful event (shots, hits, kills, damage taken/dealt, position) is
  logged once per second.

The 2-minute timer and the "score-penalty-instead-of-death" rule were
dropped. The proposal's reviewer feedback about the "100 records per feature"
rule was solved by switching to **per-second event recording inside one
session** (typically 90–300 rows per run) rather than one row per session.

### 6.2 Theme and core gameplay

- The proposal's "classic Snake with food" was redesigned around **maze
  exploration + combat**. Food and growth-on-collect were removed;
  the snake has a fixed visual length and an **HP / lives** system instead.
- A **dash** mechanic (right-click, 5 s cooldown, 2 s invincibility +
  wall-phase) was added. The proposal did not mention dashing.
- Shooting was upgraded with **lock-on aim** — the bullet steers toward the
  nearest enemy or boss within 350 px, falling back to the cursor direction
  if no target is in range. The proposal had cursor-only aim.

### 6.3 Class design

The proposal listed five classes: `Game`, `Snake`, `EnemySnake` (inheriting
from `Snake`), `Food`, `Obstacle`. The final game has a different class set
that fits the maze-shooter design:

| Proposed     | Final equivalent                          |
|--------------|-------------------------------------------|
| `Game`       | `main.py` (loop) + `StatsTracker` (data)  |
| `Snake`      | `Snake` (kept, but no growth-on-eat)      |
| `EnemySnake` | `Enemy` and `Boss` (no inheritance — different behaviour) |
| `Food`       | `Item` (ammo / key / missile pickups)     |
| `Obstacle`   | replaced by maze walls (in `maze.py`)     |
| —            | `Bullet`, `Camera`, `Particle`, `DamageNumber`, `Exit` (new) |

The boss became its own class (`Boss`) rather than an `EnemySnake` subclass
because its behaviour — three phases, knockback, summon waves, charged rifle —
shares almost nothing with normal enemy AI.

### 6.4 Boss design

The proposal did not include a boss fight at all. The **Void Sovereign**
(level 3) was added with three phases driven by HP thresholds:

- **Phase 0 (HP 120–81)** — 8-way spiral bullet pattern.
- **Phase 1 (HP 80–41)** — aimed 5-shot bursts, 6 orbiting orbs, summons
  enemies on entry and periodically.
- **Phase 2 (HP 40–0)** — dense 12-way spiral plus a charged **rifle attack**
  every 13 s: 3 s aim with a red dashed line and countdown ring, then a
  single wall-piercing bullet at 1.5× normal speed.

An earlier draft used a rotating laser beam for phase 2 instead of the rifle;
this was changed because the laser was hard to telegraph clearly within the
maze, while the rifle's dashed aim line gives a much more readable warning.

### 6.5 Statistical data

The proposal listed six features (Time, Score, Food Collected, Shooting
Count, Kill Count, Hit Accuracy, Death Count) recorded once per second for
120 seconds.

The final schema has **13 columns** per row, recorded once per second for
the full duration of a run (no fixed 120-second cap):

`session_id, t, level, hp, lives, pos_x, pos_y, shots, hits, dmg_dealt,
dmg_taken, kills, event`

Key differences:

- **No "Score" column** — the game no longer has a continuous score. The
  KPI panel computes outcome, survival time, accuracy, kills, and deaths
  directly from the per-second columns.
- **Counters are per-second deltas, not cumulative** — this makes histograms
  and bar charts (like Graph A: shots-per-20-second-window) trivial to
  compute, and cumulative views remain easy to derive by summing.
- **`pos_x` / `pos_y` were added** to enable the movement heatmap (Graph B).
- **`dmg_dealt` / `dmg_taken` were added** to enable the damage-balance
  stacked area (Graph C).
- **`event` column** captures one-off markers (`lost_life`,
  `key_collected`, `ammo_collected`, `missile_hit`, `victory`,
  `game_over:CAUSE`) used by the timeline's vertical markers.

### 6.6 Visualisation plan

The proposal's three planned charts (Score-vs-Time line, Hit-Accuracy
histogram, Shooting-vs-Kill scatter) became a **5-KPI + 4-chart dashboard**:

| Proposed                           | Final                                      |
|------------------------------------|--------------------------------------------|
| Score vs Time (line)               | **Performance Timeline** — HP/Lives line + cumulative kills line + level bands + event markers (covers time-series category) |
| Hit-Accuracy histogram             | **Graph A — Shooting Activity** (shots per 20 s, bar)  |
| Shooting-vs-Kill scatter           | **Graph B — Movement Heatmap** (pos_x × pos_y, scatter) |
| —                                  | **Graph C — Damage Balance** (10 s windows, stacked area) — new |
| —                                  | **5 KPI cards** — Outcome (with death cause), Survived, Accuracy, Kills, Deaths |

Hit accuracy moved from a chart to a KPI card (a single number is more
informative than a histogram for a single session). The shooting-vs-kill
scatter was dropped because the timeline's cumulative-kills line already
shows the same information across time. The movement heatmap and damage
balance were added because they answer behavioural questions ("where did I
hide?", "when did the fight tip against me?") that were not addressed in
the original plan.

### 6.7 Other additions not in the proposal

- **Pause menu** (ESC) with Resume / Tutorial / Quit-to-Menu / Quit-Game
  options, including a clear warning that quitting mid-run discards the
  session's stats.
- **Tutorial scene** accessible from the main menu and the pause menu.
- **Level-transition screen** showing 3 indicator nodes (two circles + a
  skull for the boss) and the player's carried-over stats, displayed for
  4 seconds before each level.
- **Phase-transition cinematic** with shockwave + ray + name reveal,
  played for 2 seconds when the boss enters a new phase. Enemies and the
  boss freeze during it; the player can still move.
- **Damage numbers** that float and fade above any target that takes a
  hit (`-1` for bullets, `-8` for missiles).
- **Session retention policy** — the latest 5 completed sessions are kept
  on disk; older sessions are trimmed automatically. Quitting mid-run does
  not save.

---

## 7. External Sources

- **pygame 2.6.1** — game runtime. <https://www.pygame.org/>
  License: LGPL.
- All code, art, sound, and game design in this repository are original work
  by the project author. No third-party assets are used.
