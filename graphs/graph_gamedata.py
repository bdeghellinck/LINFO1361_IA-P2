import matplotlib.pyplot as plt
import numpy as np

# ==========================================
# 1. DONNÉES
# ==========================================
versions = [
    "v1:\nPremier essai",
    "v2:\nModif sym_win",
    "v3:\nAdapt. poids",
    "v4:\nTemps (v1)",
    "v5:\nTemps (v2)",
    "v6:\nIterative\ndeepening",
    "v7:\nCoup d'entrée"
]

# Taux de victoire
total_win = [30, 70, 20, 30, 60, 60, 60]
first_player_win = [20, 60, 40, 20, 60, 80, 60]
second_player_win = [40, 80, 0, 40, 60, 40, 60]

# --- REMPLISSEZ CES LISTES AVEC VOS DONNÉES ---
# Exemple de données factices pour que le code fonctionne :
avg_game_time = [45, 60, 20, 180, 150, 160, 150] 
avg_turn_time = [2.5, 3.5, 1.2, 10.5, 8.8, 9.5, 8.8] 

x = np.arange(len(versions)) # Positions sur l'axe X

# ==========================================
# GRAPHIQUE 1 : Taux de réussite
# ==========================================
plt.figure(figsize=(10, 7))

# Création des 3 barres pour chaque version
plt.plot(x, total_win, marker='o', color='#1f77b4', linewidth=2, markersize=8, label='Total des parties gagnées')
plt.plot(x, first_player_win, marker='s', color='#ff69b4', linestyle='--', markersize=5, label='Pink player')
plt.plot(x, second_player_win, marker='s', color='#000000', linestyle='--', markersize=5, label='Black player')

for i, txt in enumerate(total_win):
    plt.annotate(f"{txt}%", (x[i], total_win[i]), 
                 textcoords="offset points", xytext=(0, 10), ha='center', color='#1f77b4')


plt.title("Évolution des taux de victoire contre l'agent inginious", fontsize=14, pad=15)
plt.ylabel("Taux de victoire (%)", fontsize=12)
plt.xticks(x, versions, rotation=45, ha="right", fontsize=10)
plt.ylim(0, 100)
plt.legend(loc='upper left')
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('graphs/graph1_evolution-ab_win.png', dpi=300)

# ==========================================
# GRAPHIQUE 2 & 3 : Temps de jeu et temps par tour moyen
# ==========================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), sharex=True)

ax1.plot(x, avg_game_time, marker='s', color='#1f77b4', linewidth=2, markersize=5)

for i, txt in enumerate(avg_game_time):
    ax1.annotate(f"{txt}s", (x[i], avg_game_time[i]), 
                 textcoords="offset points", xytext=(0, 10), ha='center')

ax1.set_title("Évolution de la durée moyenne d'une partie", fontsize=14, pad=15)
ax1.set_ylabel("Temps moyen (secondes)", fontsize=12)
ax1.set_xticks(x, versions, rotation=45, ha="right", fontsize=10)
ax1.set_ylim(0, 300)
ax1.grid(axis='y', linestyle='--', alpha=0.7)

ax2.plot(x, avg_turn_time, marker='s', color='#ff7f0e', linewidth=2, markersize=5)

for i, txt in enumerate(avg_turn_time):
    ax2.annotate(f"{txt}s", (x[i], avg_turn_time[i]), 
                 textcoords="offset points", xytext=(0, 10), ha='center')

ax2.set_title("Évolution du temps de calcul moyen par tour", fontsize=14, pad=15)
ax2.set_ylabel("Temps par tour (secondes)", fontsize=12)
ax2.set_xticks(x, versions, rotation=45, ha="right", fontsize=10)
ax2.set_ylim(0, 300)
ax2.grid(axis='y', linestyle='--', alpha=0.7)

plt.tight_layout()
plt.savefig('graphs/graph2_evolution-ab_temps.png', dpi=300)

plt.show() # Affiche les 3 graphiques d'un coup