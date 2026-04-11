import matplotlib.pyplot as plt

# Conditions initiales
initial_time = 300  # 5 minutes de temps total
remaining_time = initial_time
decay = 1.2

turns_played_list = []
remaining_time_list = []
time_limit_list = []  # Pour voir combien de temps est autorisé par tour

for turns_played in range(18): # Boucle de 0 à 17 tours (17 = dernier tour)
    turns_played_list.append(turns_played)
    remaining_time_list.append(remaining_time)
    
    nrem = max(17 - turns_played, 1)
    
    # Calcul de la limite de temps pour le tour actuel selon votre formule
    time_limit = remaining_time * (1 - decay**(-1)) / (1 - decay**(-nrem))
    time_limit_list.append(time_limit)
    
    # Mise à jour du temps restant pour le prochain tour
    remaining_time -= time_limit

# Configuration du graphique
plt.figure(figsize=(10, 6))

# Ligne du temps restant
plt.plot(turns_played_list, remaining_time_list, marker='o', color='#1f77b4', linewidth=2, label='Temps restant global')

# Ligne du temps alloué par tour (très utile pour le rapport !)
plt.plot(turns_played_list, time_limit_list, marker='s', color='#ff7f0e', linestyle='--', label='Temps alloué pour le tour (time_limit)')

plt.title('Gestion dynamique du temps (decay = 1.2)', fontsize=14)
plt.xlabel('turns_played', fontsize=12)
plt.ylabel('time [s]', fontsize=12)
plt.xticks(range(18)) # Affiche tous les tours de 0 à 17 sur l'axe X
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(fontsize=11)
plt.tight_layout()

# Sauvegarde l'image
plt.savefig('graphs/graph3_timefunction.png', dpi=300)
plt.show()