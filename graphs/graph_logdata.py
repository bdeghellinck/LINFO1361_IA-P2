"""
graph_logdata.py  <folder_with_csvs>

Reads all *.csv files produced by logdata.py from the given folder.
Saves 4 individual graphs in a graphs/ subfolder.

Graphs:
  graph1_taux_victoires.png
  graph2_temps_moyen_jeu.png
  graph3_temps_moyen_tour.png
  graph4_nombre_coups.png
"""

import csv
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


# ── Load CSVs ──────────────────────────────────────────────────────────────────

def load_csv(path):
    per_game, summary = [], None
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            s = row.get("section", "").strip()
            if s == "per_game":
                per_game.append(row)
            elif s == "summary":
                summary = row
    return summary, per_game


def load_folder(folder):
    results = []
    for csv_path in sorted(Path(folder).glob("*.csv")):
        summary, per_game = load_csv(csv_path)
        if summary is None:
            continue
        results.append((summary["agent"], summary, per_game))
    return results


def f(val):
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


# ── Shared style ───────────────────────────────────────────────────────────────

BLUE   = "#1f77b4"
PINK   = "#ff69b4"
BLACK  = "#222222"
ORANGE = "#ff7f0e"

def apply_style(ax, x, labels):
    ax.set_xticks(x)
    for i in range(len(labels)):
        if labels[i] == 'Agent 1':
            labels[i] = "v1:\nPremier essai"
        elif labels[i] == "Agent 2":
            labels[i] = "v2:\nModif sym_win"
        elif labels[i] == "Agent 4":
            labels[i] = "v3:\nGestion du temps"
        elif labels[i] == "Agent 6":
            labels[i] = "v4:\nGestion du temps 2"
        elif labels[i] == "Agent 7":
            labels[i] = "v5:\nIterative deepening"
        elif labels[i] == "Agent 8":
            labels[i] = "v6:\nCoup d'entrée"
        elif labels[i] == "Agent 9":
            labels[i] = "v7:\nv4 + coup d'entrée"
        else:
            pass

    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.5)


# ── Graphs ─────────────────────────────────────────────────────────────────────

def graph1_win_rate(data, out_dir, opponent):
    agents     = [d[0] for d in data]
    wr_total   = [f(d[1]["win_rate_total"])    * 100 for d in data]
    wr_pink    = [f(d[1]["win_rate_as_pink"])   * 100 for d in data]
    wr_black   = [f(d[1]["win_rate_as_black"])  * 100 for d in data]
    x = np.arange(len(agents))
    
    fig, ax = plt.subplots(figsize=(10, 7))

    ax.plot(x, wr_total, marker="o", color=BLUE,  linewidth=2, markersize=8,
            label="Total des parties gagnées")
    ax.plot(x, wr_pink,  marker="s", color=PINK,  linewidth=1.5, markersize=5,
            linestyle="--", label="Pink player")
    ax.plot(x, wr_black, marker="s", color=BLACK, linewidth=1.5, markersize=5,
            linestyle="--", label="Black player")

    for i, v in enumerate(wr_total):
        ax.annotate(f"{v:.0f}%", (x[i], v),
                    textcoords="offset points", xytext=(0, 10),
                    ha="center", color=BLUE, fontsize=10, bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.5, edgecolor=BLUE))

    ax.set_title(f"Taux de victoires (%) contre l'agent {opponent}", fontsize=14, pad=15)
    ax.set_ylabel("Taux de victoire (%)", fontsize=12)
    ax.set_ylim(0, 100)
    ax.legend(loc="upper left")
    apply_style(ax, x, agents)
    fig.tight_layout()
    path = out_dir / "graph1_taux_victoires.png"
    fig.savefig(path, dpi=300)
    plt.close(fig)
    print(f"  Saved -> {path}")


def graph2_avg_game_time(data, out_dir, opponent):
    agents   = [d[0] for d in data]
    avg_my_time = [f(d[1]["avg_my_time"]) for d in data]
    avg_opp_time = [f(d[1]["avg_opp_time"]) for d in data]
    avg_game_time = [f(d[1]["avg_game_time"]) for d in data]
    
    for i in range(len(avg_game_time)):
        avg_game_time[i] = avg_game_time[i]/2
        
    x = np.arange(len(agents))

    fig, ax = plt.subplots(figsize=(10, 7))

    ax.plot(x, avg_my_time, marker="s", color=BLUE, linewidth=2, markersize=5, label="Mon temps")
    ax.plot(x, avg_opp_time, marker="s", color=ORANGE, linewidth=2, markersize=5, label="Temps de l'adversaire")
    ax.plot(x, avg_game_time, marker="s", color=BLACK, linewidth=2, markersize=5, label="Temps total du jeu divisé par 2")
    for i, v in enumerate(avg_my_time):
        ax.annotate(f"{v:.1f}s", (x[i], v),
                    textcoords="offset points", xytext=(0, 10), color=BLUE,
                    ha="center", fontsize=10, bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.5, edgecolor=BLUE))

    ax.set_title(f"Temps moyen de jeu contre l'agent {opponent}", fontsize=14, pad=15)
    ax.set_ylabel("Temps moyen (s)", fontsize=12)
    ax.set_ylim(0, max(max(avg_my_time), max(avg_opp_time)) * 1.25 + 1)
    ax.axhline(y=300, color='r', linestyle='--', label="Limite de temps (300s)", linewidth=1, zorder=0)
    #ax.text(0, 300, "Limite de temps (300s)", color='red', va='bottom', fontsize=9)
    ax.legend(loc="upper left")
    apply_style(ax, x, agents)
    fig.tight_layout()
    path = out_dir / "graph2_temps_moyen_jeu.png"
    fig.savefig(path, dpi=300)
    plt.close(fig)
    print(f"  Saved -> {path}")


def graph3_avg_turn_time(data, out_dir, opponent):
    agents   = [d[0] for d in data]
    avg_my_turn = [f(d[1]["avg_my_turn_summary"]) for d in data]
    avg_opp_turn = [f(d[1]["avg_opp_turn_summary"]) for d in data]
    x = np.arange(len(agents))
    
    fig, ax = plt.subplots(figsize=(10, 7))

    ax.plot(x, avg_my_turn, marker="s", color=BLUE, linewidth=2, markersize=5, label="Mon tour")
    ax.plot(x, avg_opp_turn, marker="s", color=ORANGE, linewidth=2, markersize=5, label="Tour de l'adversaire")
    for i, v in enumerate(avg_my_turn):
        ax.annotate(f"{v:.2f}s", (x[i], v),
                    textcoords="offset points", xytext=(0, 10), color=BLUE,
                    ha="center", fontsize=10, bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.5, edgecolor=BLUE))

    ax.set_title(f"Temps moyen par tour contre l'agent {opponent}", fontsize=14, pad=15)
    ax.set_ylabel("Temps par tour (s)", fontsize=12)
    ax.set_ylim(0, max(max(avg_my_turn), max(avg_opp_turn)) * 1.25 + 0.1)
    ax.legend(loc="upper left")
    apply_style(ax, x, agents)
    fig.tight_layout()
    path = out_dir / "graph3_temps_moyen_tour.png"
    fig.savefig(path, dpi=300)
    plt.close(fig)
    print(f"  Saved -> {path}")


def graph4_avg_moves(data, out_dir, opponent):
    agents   = [d[0] for d in data]
    avg_moves = [f(d[1]["avg_my_moves"]) for d in data]
    x = np.arange(len(agents))
    
    fig, ax = plt.subplots(figsize=(10, 7))

    ax.plot(x, avg_moves, marker="s", color=BLUE, linewidth=2, markersize=5)
    for i, v in enumerate(avg_moves):
        ax.annotate(f"{v:.1f}", (x[i], v),
                    textcoords="offset points", xytext=(0, 10), color=BLUE,
                    ha="center", fontsize=10, bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.5, edgecolor=BLUE))

    ax.set_title(f"Nombre de coups moyen contre l'agent {opponent}", fontsize=14, pad=15)
    ax.set_ylabel("Nombre de coups", fontsize=12)
    ax.set_ylim(0, max(avg_moves) * 1.25 + 1)
    apply_style(ax, x, agents)
    fig.tight_layout()
    path = out_dir / "graph4_nombre_coups.png"
    fig.savefig(path, dpi=300)
    plt.close(fig)
    print(f"  Saved -> {path}")


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python graphs/graph_logdata.py <folder_with_csvs>")
        sys.exit(1)

    folder = Path(sys.argv[1])
    data   = load_folder(folder)

    if not data:
        print(f"No valid CSV files found in '{folder}'")
        sys.exit(1)

    # All CSVs in the folder are against the same opponent — take from first entry
    opponent = data[0][1]["opponent"]

    print(f"  Loaded {len(data)} CSV(s) — opponent: {opponent}")
    print(f"  Agents: {', '.join(d[0] for d in data)}")

    out_dir = folder / "graphs"
    out_dir.mkdir(exist_ok=True)

    graph1_win_rate(data, out_dir, opponent)
    graph2_avg_game_time(data, out_dir, opponent)
    graph3_avg_turn_time(data, out_dir, opponent)
    graph4_avg_moves(data, out_dir, opponent)

    print(f"\n  All graphs saved in {out_dir}/")