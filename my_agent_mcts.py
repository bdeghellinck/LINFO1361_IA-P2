from agent import Agent
from oxono import Game
import random
from math import sqrt, log
import time

class Node:
    '''
    Un noeud dans l'arbre.
    Représente un état du jeu avec les nombres de victoire et de passage associé.
    '''
    __slots__ = ('victoire', 'passage', 'enfants', 'parent', 'action', 'actions_non_expansee', 'terminal')

    def __init__(self, parent, action):
        self.victoire = 0 #Nombre de victoire total
        self.passage = 0 #Nombre fois ou on est passé dans le noeud
        #self.state = state #Etat instantane de la partie
        #self.actions_possible = Game.actions(state) #List d'actions potentielles (qui n'ont pas été expansé)
        self.enfants = [] #Liste des Noeuds exploré 
        self.parent = parent #Noeud precedent (juste au dessus dans l'arbre)
        self.action = action #Action du noeud parent pour arriver au noeud actuelle
        # self.index_action = 0 #Index pour la prochaine action non expansé
        self.actions_non_expansee = None
        self.terminal = False


    # def prochaine_action(self):
    #     '''
    #     Prochaine action à expansée
    #     '''
    #     action = self.actions_possible[self.index_action]
    #     self.index_action += 1

    #     if self.index_action >= len(self.actions_possible):
    #         self.actions_possible = None

    #     return action

def calcul_ucb1(node, passage_parent):
    '''
    Utile pour l'etape 1
    Calcule le ucb1.
    Pour favoriser les noeuds qu'on visite pour la 1ere fois avec une valeur infini.
    c est la constante d'exploration et peut être changé pour ajuster l'exploration à l'exploitation
    '''
    c = sqrt(2) #Valeur par défaut
    if node.passage == 0:
        return float('inf')
    else:
        # wi / ni + c * sqrt( ln(N) / ni )
        return node.victoire/ node.passage + c * sqrt(log(passage_parent) / node.passage)
    
def selection(racine, state_racine):
    '''
    Utile pour l'etape 1
    Avance dans l'arbre, en choisisant l'enfant avec le meilleur ucb1,
    jusqu'a la fin de la partie ou lorsqu'un noeud avec des action non expansée est trouvé
    '''
    node = racine
    state = state_racine.copy()


    while True:
        if node.terminal: return node, state

        if node.actions_non_expansee is None:
            actions = Game.actions(state)
            if not actions:
                node.terminal = True
                return node, state
            random.shuffle(actions)
            node.actions_non_expansee = actions

        if node.actions_non_expansee: return node, state

        if not node.enfants:
            node.terminal = True
            return node, state
        
        node = max( node.enfants, key=lambda n:calcul_ucb1(n, node.passage) )
        Game.apply(state, node.action)

def expension(node, state):
    '''
    Utile pour l'etape 2
    Avec une action non expansée (dans le noeud), on crée un nouveau noeud.
    '''
    action_n_e = node.actions_non_expansee.pop() #Prends un action non expansée
    nouvelle_etat = state.copy() #Prends l'état actuelle de la partie
    Game.apply( nouvelle_etat, action_n_e ) #Exerce l'action choisi sur la partie 
    nouvelle_enfant = Node(node, action_n_e ) #Ceci crée un nouvelle noeud qui offre apres, possiblement, d'autres choix possible
    node.enfants.append(nouvelle_enfant)
    return nouvelle_enfant, nouvelle_etat

def simulation(state, player):
    '''
    Utile pour l'étape 3
    A partir du nouveau noeud, on jour la partie de maniere aléatoire jusqu'à ce que la partie ce termine (une condition gagnante ou égailité)
    ou jusqu'a un palier, pour eviter de consommer trop de temps et memoire
    '''
    state = state.copy()
    palier_max = 30
    palier = 0
    while not Game.is_terminal(state) and palier < palier_max:
        action_aleatoire = random.choice( Game.actions(state) ) #Prends une action dans la liste d'actions
        Game.apply(state,action_aleatoire) #Joue avec cette action
        palier += 1
    return Game.utility(state, player) #1 si le jouer a gagné, -1 si perdu, 0 is égalité

def retropropagation(node, score):
    '''
    Utile pour l'étape 4
    Le résultat remonde l'arbre et mets a jour le nombre de visite et de victoire 
    '''
    while node is not None:
        node.passage += 1
        node.victoire += score
        node = node.parent
    
import tracemalloc
 

class My_MCTS_Agent(Agent):
    #Pour limiter la taille de l'abre:
    Nbr_Max_Nodes = 80000

    def __init__(self, player):
        super().__init__(player)
        self.moves_done = 0
    
    def act(self, state, remaining_time):

        #Calcul du temps pour le tour
        alpha = 2 #Base de décroisante(plus c'est grand, plus ca décroit vite)
        k = self.moves_done 
        Nrem = max(18 - k,1) #Nombre de coup encore possible (36 cases donc 18 coups total possible par joueur)
        temps_du_tour = remaining_time * (1 - alpha**(-1)) / (1 - alpha**(-Nrem))
        temps_max = time.perf_counter() + temps_du_tour
        self.moves_done += 1

        #Départ de la racine
        racine = Node(None, None)
        Nbr_nodes = 1

        while time.perf_counter() < temps_max and Nbr_nodes < self.Nbr_Max_Nodes:
            #Etape 1 - Selection
            #Descends l'abre en choisisant l'enfant qui max l'ucb1
            node, state_node = selection(racine, state)
        
            #Etape 2 - Expension
            #Quand on atteint un noeud qui n'a pas encore tout ses enfants, on en cree un nouveau
            if not node.terminal and node.actions_non_expansee:
                node, state_node = expension(node, state_node)
                Nbr_nodes += 1

            #Etape 3 - Simulation
            #On joue aléatoirement
            if Game.is_terminal(state_node):
                score = Game.utility(state_node, self.player)
                node.terminal = True
            else:
                state_simulation = state_node.copy()
                score = simulation(state_simulation, self.player)

            #Etape 4 - Retropropagtion
            #On remonte le resultat et mise a jour de l'arbre
            retropropagation(node, score)

        noeud_optimal = max(racine.enfants, key=lambda n: (n.passage))
    
        return noeud_optimal.action
