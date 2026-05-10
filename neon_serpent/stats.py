"""
stats.py
Per-second game statistics tracker (new schema).

Schema (per-second deltas, not cumulative)
-------------------------------------------
session_id, t, level, hp, lives, pos_x, pos_y,
shots, hits, dmg_dealt, dmg_taken, kills, event

`event` is one of: "" (no event), "lost_life", "phase_change", "missile_hit"

Save policy
-----------
end_session(save=True)  → append rows + keep latest 3 sessions
end_session(save=False) → discard rows (used when player quits mid-game)
"""
import csv
from pathlib import Path

CSV_PATH     = Path("game_stats.csv")
MAX_SESSIONS = 5

FIELDNAMES = [
    "session_id", "t", "level",
    "hp", "lives",
    "pos_x", "pos_y",
    "shots", "hits",
    "dmg_dealt", "dmg_taken",
    "kills", "event",
]


def _load_existing() -> list[dict]:
    if not CSV_PATH.exists():
        return []
    with open(CSV_PATH, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        # Detect old schema (time_elapsed instead of t) and discard
        if rows and "t" not in rows[0]:
            CSV_PATH.unlink(missing_ok=True)
            return []
        return rows


def _next_session_id(rows: list[dict]) -> int:
    if not rows:
        return 1
    return max(int(r["session_id"]) for r in rows) + 1


def _save(rows: list[dict]) -> None:
    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


class StatsTracker:
    """
    Tick once per second during gameplay.

    During a tick, accumulate per-second deltas:
        record_shot()  / record_hit()
        record_kill()
        record_dmg_dealt(n) / record_dmg_taken(n)

    Then call tick(snake, game) — the per-second counters are flushed.

    add_event(name) records a one-off event marker on the current second.
    """

    def __init__(self) -> None:
        self._session_rows: list[dict] = []
        self._session_id: int = 1
        self._active: bool = False
        # Per-second counters (reset each tick)
        self._shots = 0
        self._hits = 0
        self._kills = 0
        self._dmg_dealt = 0
        self._dmg_taken = 0
        self._event = ""

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start_session(self) -> None:
        existing = _load_existing()
        self._session_id   = _next_session_id(existing)
        self._session_rows = []
        self._active = True
        self._reset_counters()

    def _reset_counters(self) -> None:
        self._shots = 0
        self._hits = 0
        self._kills = 0
        self._dmg_dealt = 0
        self._dmg_taken = 0
        self._event = ""

    def end_session(self, save: bool = True) -> None:
        """
        Save=True   → merge into CSV, keep latest 3 sessions.
        Save=False  → discard rows (player quit mid-game).
        """
        if not self._active or not self._session_rows or not save:
            self._active = False
            self._session_rows = []
            return

        existing = _load_existing()
        combined = existing + self._session_rows

        # Keep only the 3 most recent session ids
        all_ids  = sorted({int(r["session_id"]) for r in combined})
        keep_ids = set(all_ids[-MAX_SESSIONS:])
        combined = [r for r in combined if int(r["session_id"]) in keep_ids]

        _save(combined)
        self._active = False
        self._session_rows = []

    # ── Per-second event recorders ────────────────────────────────────────────

    def record_shot(self) -> None:
        if self._active:
            self._shots += 1

    def record_hit(self, damage: int = 1) -> None:
        if self._active:
            self._hits += 1
            self._dmg_dealt += damage

    def record_kill(self) -> None:
        if self._active:
            self._kills += 1

    def record_dmg_taken(self, damage: int = 1) -> None:
        if self._active:
            self._dmg_taken += damage

    def add_event(self, name: str) -> None:
        """Latest event in this second wins."""
        if self._active:
            self._event = name

    # ── Tick (called once per second) ─────────────────────────────────────────

    def tick(self, snake, game: dict) -> None:
        if not self._active:
            return
        elapsed = int((pygame_ticks() - game["start"]) / 1000)
        self._session_rows.append({
            "session_id": self._session_id,
            "t":          elapsed,
            "level":      game["level"],
            "hp":         snake.hp,
            "lives":      snake.lives,
            "pos_x":      int(snake.head.x),
            "pos_y":      int(snake.head.y),
            "shots":      self._shots,
            "hits":       self._hits,
            "dmg_dealt":  self._dmg_dealt,
            "dmg_taken":  self._dmg_taken,
            "kills":      self._kills,
            "event":      self._event,
        })
        self._reset_counters()

    # ── Read API for analytics screen ─────────────────────────────────────────

    def has_data(self) -> bool:
        return CSV_PATH.exists() and CSV_PATH.stat().st_size > 10

    def load_sessions(self) -> dict[int, list[dict]]:
        rows = _load_existing()
        result: dict[int, list[dict]] = {}
        for r in rows:
            sid = int(r["session_id"])
            result.setdefault(sid, []).append(r)
        return result


def pygame_ticks() -> int:
    import pygame
    return pygame.time.get_ticks()
