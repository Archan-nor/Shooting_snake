# Visualization Documentation

This file documents all data-related visualizations for **Neon Serpent**.

> **Note:** Replace the placeholder descriptions below with actual screenshots
> and explanations once the data/statistics page is implemented.

---

## Data Visualization Page — Overall View

![Overall visualization page](overall.png)

The statistics screen displays per-session gameplay data collected during each run.
It is accessible from the main menu after completing at least one game. The page
shows a summary table at the top and three charts below it.

---

## Component 1 — Session Summary Table

![Session summary table](table_summary.png)

The table lists each completed session with columns for Date, Level Reached,
Kills, Keys Collected, Survival Time (seconds), and Outcome (Win / Death cause).
Each row represents one game run, allowing players to compare performance over time.

---

## Component 2 — Kills Per Session (Bar Chart)

![Kills per session bar chart](chart_kills.png)

A bar chart plotting total enemy kills on the Y-axis against session number on the
X-axis. Bars are colour-coded cyan (C_AMMO palette) to match the in-game ammo
aesthetic. This chart makes it easy to spot improvement trends in combat efficiency.

---

## Component 3 — Survival Time Distribution (Histogram)

![Survival time histogram](chart_survival.png)

A histogram of survival durations across all sessions, grouped into 15-second bins.
The distribution reveals whether most players die early, mid-run, or survive to the
boss fight, informing future difficulty-tuning decisions.

---

## Component 4 — Death Causes (Pie Chart)

![Death causes pie chart](chart_death.png)

A pie chart breaking down how players died: Wall Collision, Overwhelmed by Enemies,
Consumed by Enemies, Incinerated by Laser. Understanding the most common death types
guides balancing of enemy density, boss laser timing, and maze complexity.
