# Data Visualization

This folder documents the in-game **Data Analytics** screen. The dashboard
is reached from the main menu (the **DATA ANALYTICS** button is enabled once
at least one completed session has been saved to `game_stats.csv`).

The dashboard always shows **one selected session** at a time. The `<` / `>`
buttons at the top of the screen step through the 5 most recent sessions; the
header reads `Latest session • WIN` (or `LOST`), then `1 session ago`,
`2 sessions ago`, and so on, plus a `(N/M)` index.

All sessions are drawn from `game_stats.csv`, which is written by the
`StatsTracker` class (`neon_serpent/stats.py`). Each row of the CSV is one
gameplay second; counters (shots / hits / damage / kills) are stored as
per-second deltas, which makes time-series and distribution charts straightforward.

---

## Overall page

![Analytics overview](overall.png)

The dashboard is organised top-to-bottom as **header → KPIs → timeline →
three small graphs**. The vertical flow follows a typical post-game
debrief: *Did I win or lose? How long did I survive? How well did I play?*
followed by detail charts that explain *why*.

---

## 1. KPI cards

![KPI cards](kpi_cards.png)

Five KPI cards summarise the entire run at a glance.

- **Outcome** — `WIN` (green) or `LOST` (red). When the run ended in a loss,
  the death cause appears as a subtitle below the value (`WALL COLLISION`,
  `OVERWHELMED BY ENEMIES`, `INCINERATED BY LASER`, etc.). The cause comes
  from the `event` column of the final row, encoded as `game_over:<cause>`.
- **Survived** — total seconds the player was alive, computed from
  `max(t)` in the session.
- **Accuracy** — `hits / max(shots, 1) × 100 %`, clamped to 100 %. Missile
  pickups are deliberately excluded from `hits` so the percentage cannot
  exceed the number of actual bullets fired.
- **Kills** — `sum(kills)` for the session.
- **Deaths** — number of lives lost, computed as `MAX_LIVES − min(lives)`.
  This is more reliable than counting `lost_life` events because the very
  last death is captured by the `game_over` event row instead of a `lost_life`
  row.

---

## 2. Performance Timeline

![Performance timeline](timeline.png)

The timeline is the dashboard's main story-telling chart. It combines several
layers on a single time axis:

- **Three level bands** in the background (`LEVEL 1`, `LEVEL 2`, `BOSS`),
  separated by white dashed vertical dividers. Bold labels sit at the top of
  each band so the boss section is unmistakable.
- A **red HP / Lives line** (left Y axis, 0 to MAX_LIVES). Y gridlines mark
  every 2 lives; minor lines mark each HP unit within a life so you can read
  damage events precisely.
- A **green cumulative-kills line** (right Y axis), giving a sense of pace —
  steep slope = killing fast, flat = waiting / collecting.
- **Triangular event markers** at the top of the chart for one-off events:
  red = `lost_life`, yellow = `key_collected`, cyan = `ammo_collected`,
  orange = `missile_hit`. A vertical dashed line drops from each marker
  through the plot so you can read the exact moment.
- A **legend strip** under the title spells out every line and marker colour.

This single chart is enough to reconstruct the broad arc of any session — when
the player took damage, when they switched levels, and how aggressively they
were clearing enemies.

---

## 3. Graph A — Shooting Activity

![Graph A: Shooting Activity](graph_a_shooting.png)

A bar chart showing **total shots fired per 20-second window**.

- X axis is divided into 20 s buckets. Tick marks are drawn every 20 s; labels
  appear on every other tick to avoid crowding (`20s`, `40s`, `60s`, …).
- Y axis is the total `shots` summed across all rows whose `t // 20` falls in
  that bucket.
- The subtitle below the graph repeats the axis legend in plain text.

The chart answers questions like *did I shoot in steady bursts, or panic-fire
when the boss showed up?* A flat baseline followed by a tall spike usually
indicates a phase change or a key fight; an even profile is the sign of a
disciplined player.

---

## 4. Graph B — Movement Heatmap

![Graph B: Movement Heatmap](graph_b_heatmap.png)

A scatter plot of every recorded `(pos_x, pos_y)` sample, drawn with a
semi-transparent cyan dot. Where the player lingered, dots overlap and the
cell looks brighter; where they passed through quickly, dots are sparse.

- Coordinates are world-space pixels (0 to 1400 horizontally, 0 to 800
  vertically). Corner labels show the bounds.
- Each frame uses one row from the CSV, so the density is proportional to
  *time spent* in that area, not just *visits*.

The heatmap exposes movement habits — players often unconsciously orbit a
favourite corner or hug a particular wall. The boss arena (centre of level 3)
typically shows up as a clear dense spot near the middle.

---

## 5. Graph C — Damage Balance

![Graph C: Damage Balance](graph_c_damage.png)

A stacked area chart of **damage taken vs damage dealt**, aggregated into
10-second windows.

- The **red area at the bottom** is `dmg_taken` per window.
- The **green area stacked on top** is `dmg_dealt`. The total height
  represents the combined damage activity in that window.
- The Y axis auto-scales to the largest value in the session (rounded up to a
  nice multiple of 5, 10, or 20) so the chart never overflows the panel.
- The same three level bands and dashed dividers from the timeline are drawn
  here, so you can see at a glance how each level's damage profile differs.
- X tick marks are drawn every 10 s; labels appear every 4 ticks to stay readable.
- The legend in the subtitle uses coloured swatches (🟩 dealt, 🟥 taken)
  instead of words, matching the area colours.

This is the dashboard's "balance sheet." A healthy run shows mostly green
with slim red bands; a struggling run shows red catching up with green,
especially in the boss section.

---

## How to read the dashboard, in summary

1. **Glance at the KPI row** for the verdict and the headline numbers.
2. **Read the timeline** to see the shape of the run — when you lost lives,
   how kills accumulated, when level transitions happened.
3. **Drill into the three small graphs** for behavioural detail:
   *Graph A* (shooting cadence), *Graph B* (positioning), *Graph C* (damage trade).

The four charts cover the four chart categories required by the rubric:

| Chart | Type           | Category       |
|-------|----------------|----------------|
| Timeline | Line graph  | Time-series    |
| A     | Bar graph      | Distribution / Time-series |
| B     | Scatter plot   | Relation       |
| C     | Stacked area   | Proportion     |
