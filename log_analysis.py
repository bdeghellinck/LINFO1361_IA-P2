"""
analyze_logs.py  <path/to/combined_file.txt>

Parses a combined game-log file, prints a text report, and writes a CSV
next to the input file (same stem, .csv extension).

CSV layout:
  - per-game rows  (section=per_game)
  - one blank row
  - summary row    (section=summary)
  All rows share the same columns (union of all fields; unused cells empty).
"""

import csv
import re
import sys
from pathlib import Path


MOVE_RE = re.compile(
    r"\(\s*'([XO])'\s*,\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)\s*,"
    r"\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)\s*\)\s*,\s*([\d.eE+\-]+)"
)

# Single unified fieldname list used for every row
FIELDS = [
    "section",
    # identifiers
    "agent", "opponent",
    # per-game fields
    "game_number", "role",
    "num_moves", "my_num_moves", "opp_num_moves",
    "my_total_time", "opp_total_time", "game_total_time",
    "my_avg_turn", "opp_avg_turn",
    "my_max_turn", "opp_max_turn",
    "my_last_remaining", "opp_last_remaining",
    "result", "timeout",
    # summary-only fields
    "num_games",
    "win_rate_total", "win_rate_as_pink", "win_rate_as_black",
    "avg_game_time", "avg_my_time", "avg_opp_time",
    "avg_my_turn_summary", "avg_opp_turn_summary",
    "avg_my_moves", "avg_opp_moves",
    "my_timeouts", "opp_timeouts",
    "best_win_streak",
]


# ── Parsing ────────────────────────────────────────────────────────────────────

def parse_combined_file(filepath):
    text = Path(filepath).read_text()
    lines = [l.rstrip() for l in text.splitlines()]

    log_marker_re = re.compile(r"^log_(\d+)\.txt$", re.IGNORECASE)
    markers = [(i, int(m.group(1))) for i, l in enumerate(lines)
               if (m := log_marker_re.match(l))]

    if not markers:
        raise ValueError("No 'log_N.txt' markers found in the file.")

    games = []
    for idx, (start_line, game_number) in enumerate(markers):
        end_line = markers[idx + 1][0] if idx + 1 < len(markers) else len(lines)
        block = [l for l in lines[start_line + 1: end_line] if l.strip()]

        if len(block) < 2:
            continue
        try:
            max_time = float(block[0])
        except ValueError:
            continue

        i_go_first = game_number < 5

        moves = []
        for line in block[2:]:
            m = MOVE_RE.match(line)
            if m:
                moves.append({
                    "piece":     m.group(1),
                    "from":      (int(m.group(2)), int(m.group(3))),
                    "to":        (int(m.group(4)), int(m.group(5))),
                    "remaining": float(m.group(6)),
                })
        if not moves:
            continue

        my_idx  = range(0, len(moves), 2) if i_go_first else range(1, len(moves), 2)
        opp_idx = range(1, len(moves), 2) if i_go_first else range(0, len(moves), 2)

        def turn_times_for(indices):
            times, lst = [], list(indices)
            for rank, idx in enumerate(lst):
                mv = moves[idx]
                spent = (max_time if rank == 0 else moves[lst[rank-1]]["remaining"]) - mv["remaining"]
                times.append(max(spent, 0.0))
            return times

        my_tt  = turn_times_for(my_idx)
        opp_tt = turn_times_for(opp_idx)

        my_last  = moves[list(my_idx)[-1]]["remaining"]  if my_idx  else max_time
        opp_last = moves[list(opp_idx)[-1]]["remaining"] if opp_idx else max_time

        if my_last <= 0:
            i_won, timeout = False, True
        elif opp_last <= 0:
            i_won, timeout = True, True
        else:
            i_won   = ((len(moves) - 1) % 2 == 0) == i_go_first
            timeout = False

        my_total  = sum(my_tt)
        opp_total = sum(opp_tt)

        games.append({
            "game_number":    game_number,
            "max_time":       max_time,
            "i_go_first":     i_go_first,
            "num_moves":      len(moves),
            "my_num_moves":   len(my_tt),
            "opp_num_moves":  len(opp_tt),
            "my_turn_times":  my_tt,
            "opp_turn_times": opp_tt,
            "my_avg_turn":    my_total  / len(my_tt)  if my_tt  else 0,
            "opp_avg_turn":   opp_total / len(opp_tt) if opp_tt else 0,
            "my_max_turn":    max(my_tt)  if my_tt  else 0,
            "opp_max_turn":   max(opp_tt) if opp_tt else 0,
            "my_total":       my_total,
            "opp_total":      opp_total,
            "game_total":     my_total + opp_total,
            "i_won":          i_won,
            "timeout":        timeout,
            "my_last":        my_last,
            "opp_last":       opp_last,
        })

    return games


# ── Title helpers ──────────────────────────────────────────────────────────────

def prettify(s):
    s = re.sub(r'[_\-]+', ' ', s)
    s = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', s)
    return s.strip().title()

def make_title(filepath):
    p = Path(filepath)
    agent  = prettify(p.stem)
    folder = prettify(p.parent.name) if p.parent.name else '.'
    return agent, folder


# ── CSV export ─────────────────────────────────────────────────────────────────

def write_csv(games, filepath):
    p = Path(filepath)
    agent, opponent = make_title(filepath)
    csv_path = p.with_suffix(".csv")

    n           = len(games)
    first_g     = [g for g in games if     g["i_go_first"]]
    second_g    = [g for g in games if not g["i_go_first"]]
    wins_total  = sum(1 for g in games   if g["i_won"])
    wins_first  = sum(1 for g in first_g if g["i_won"])
    wins_second = sum(1 for g in second_g if g["i_won"])
    all_my      = [t for g in games for t in g["my_turn_times"]]
    all_opp     = [t for g in games for t in g["opp_turn_times"]]
    streak = cur = 0
    for g in games:
        cur = cur + 1 if g["i_won"] else 0
        streak = max(streak, cur)

    empty = {f: "" for f in FIELDS}

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()

        for g in sorted(games, key=lambda x: x["game_number"]):
            row = {**empty,
                "section":           "per_game",
                "agent":             agent,
                "opponent":          opponent,
                "game_number":       g["game_number"],
                "role":              "pink" if g["i_go_first"] else "black",
                "num_moves":         g["num_moves"],
                "my_num_moves":      g["my_num_moves"],
                "opp_num_moves":     g["opp_num_moves"],
                "my_total_time":     round(g["my_total"],     4),
                "opp_total_time":    round(g["opp_total"],    4),
                "game_total_time":   round(g["game_total"],   4),
                "my_avg_turn":       round(g["my_avg_turn"],  4),
                "opp_avg_turn":      round(g["opp_avg_turn"], 4),
                "my_max_turn":       round(g["my_max_turn"],  4),
                "opp_max_turn":      round(g["opp_max_turn"], 4),
                "my_last_remaining": round(g["my_last"],      4),
                "opp_last_remaining":round(g["opp_last"],     4),
                "result":            "win" if g["i_won"] else "loss",
                "timeout":           g["timeout"],
            }
            writer.writerow(row)

        writer.writerow(empty)  # blank separator

        writer.writerow({**empty,
            "section":           "summary",
            "agent":             agent,
            "opponent":          opponent,
            "num_games":         n,
            "win_rate_total":    round(wins_total  / n,               4) if n           else 0,
            "win_rate_as_pink":  round(wins_first  / len(first_g),    4) if first_g     else "",
            "win_rate_as_black": round(wins_second / len(second_g),   4) if second_g    else "",
            "avg_game_time":     round(sum(g["game_total"] for g in games) / n, 4),
            "avg_my_time":       round(sum(g["my_total"]   for g in games) / n, 4),
            "avg_opp_time":      round(sum(g["opp_total"]  for g in games) / n, 4),
            "avg_my_turn_summary":  round(sum(all_my)  / len(all_my),  4) if all_my  else 0,
            "avg_opp_turn_summary": round(sum(all_opp) / len(all_opp), 4) if all_opp else 0,
            "avg_my_moves":      round(sum(g["my_num_moves"]  for g in games) / n, 2),
            "avg_opp_moves":     round(sum(g["opp_num_moves"] for g in games) / n, 2),
            "my_timeouts":       sum(1 for g in games if g["timeout"] and not g["i_won"]),
            "opp_timeouts":      sum(1 for g in games if g["timeout"] and     g["i_won"]),
            "best_win_streak":   streak,
        })

    print(f"  CSV written -> {csv_path}")
    return csv_path


# ── Text report ────────────────────────────────────────────────────────────────

def pct(num, den):
    return f"{100 * num / den:.1f}%" if den else "N/A"

def print_report(games, filepath=""):
    n = len(games)
    if n == 0:
        print("No valid game logs found.")
        return

    agent, opponent = make_title(filepath) if filepath else ("?", "?")
    title_str = f"  GAME LOG ANALYSIS  —  {n} game(s)  —  {agent} vs {opponent}"
    sep2 = "═" * max(54, len(title_str) + 2)
    sep  = "─" * len(sep2)

    avg_game = sum(g["game_total"] for g in games) / n
    avg_my   = sum(g["my_total"]   for g in games) / n
    avg_opp  = sum(g["opp_total"]  for g in games) / n

    all_my  = [t for g in games for t in g["my_turn_times"]]
    all_opp = [t for g in games for t in g["opp_turn_times"]]
    avg_my_turn  = sum(all_my)  / len(all_my)  if all_my  else 0
    avg_opp_turn = sum(all_opp) / len(all_opp) if all_opp else 0

    first_g  = [g for g in games if     g["i_go_first"]]
    second_g = [g for g in games if not g["i_go_first"]]
    wins_total  = sum(1 for g in games    if g["i_won"])
    wins_first  = sum(1 for g in first_g  if g["i_won"])
    wins_second = sum(1 for g in second_g if g["i_won"])

    streak = cur = 0
    for g in games:
        cur = cur + 1 if g["i_won"] else 0
        streak = max(streak, cur)

    my_to  = sum(1 for g in games if g["timeout"] and not g["i_won"])
    opp_to = sum(1 for g in games if g["timeout"] and     g["i_won"])

    print(f"\n{sep2}")
    print(title_str)
    print(sep2)

    print(f"\nTIMING")
    print(sep)
    print(f"  Avg game duration  (all)  : {avg_game:>8.2f} s")
    print(f"  Avg game duration  (me)   : {avg_my:>8.2f} s")
    print(f"  Avg game duration  (opp)  : {avg_opp:>8.2f} s")
    print(f"  Avg turn time      (me)   : {avg_my_turn:>8.2f} s")
    print(f"  Avg turn time      (opp)  : {avg_opp_turn:>8.2f} s")
    print(f"  Longest turn       (me)   : {max(all_my) if all_my else 0:>8.2f} s")
    print(f"  Shortest turn      (me)   : {min(all_my) if all_my else 0:>8.2f} s")

    print(f"\nRESULTS")
    print(sep)
    print(f"  Total wins         : {wins_total:>3} / {n:<3}  ({pct(wins_total, n)})")
    if first_g:
        print(f"  Wins as 1st (pink) : {wins_first:>3} / {len(first_g):<3}  ({pct(wins_first,  len(first_g))})")
    if second_g:
        print(f"  Wins as 2nd (black): {wins_second:>3} / {len(second_g):<3}  ({pct(wins_second, len(second_g))})")
    print(f"  Best win streak    : {streak}")

    print(f"\nMOVES")
    print(sep)
    print(f"  Avg moves per game  (all)  : {sum(g['num_moves']        for g in games)/n:>8.1f}")
    print(f"  Avg moves per game  (me)   : {sum(g['my_num_moves']     for g in games)/n:>8.1f}")
    print(f"  Avg moves per game  (opp)  : {sum(g['opp_num_moves']    for g in games)/n:>8.1f}")

    print(f"\nTIMEOUTS")
    print(sep)
    print(f"  Timouts  (me)   : {my_to}")
    print(f"  Timouts  (opp)  : {opp_to}")

    print(f"\nPER-GAME BREAKDOWN")
    print(sep)
    print(f"  {'Log':<8} {'Role':>6}  {'Moves':>5}  {'My time':>8}  {'Opp time':>9}  Result")
    print("  " + "·" * 50)
    for g in sorted(games, key=lambda x: x["game_number"]):
        role   = "pink"  if g["i_go_first"] else "black"
        result = "WON" if g["i_won"] else ("lost (timeout)" if g["timeout"] else "lost")
        print(f"  log_{g['game_number']:<4} {role:>6}  {g['num_moves']:>5}"
              f"  {g['my_total']:>8.1f}s  {g['opp_total']:>8.1f}s  {result}")
    print(sep)
    print()


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analyze_logs.py <path_to_combined_file.txt>")
        sys.exit(1)
    fp = sys.argv[1]
    games = parse_combined_file(fp)
    print_report(games, filepath=fp)
    write_csv(games, fp)