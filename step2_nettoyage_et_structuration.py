# L'objectif de ce script est de nettoyer et 
# structurer les données des df_pontes et df_meteo
# La structuration passera par la création des fonctions de mapping 
# pour les poules, les météos, les températures, les humidités, les commentaires
# et les oeufs trouvés/dates de trouvaille et la création de nouvelles colonnes
# qui permettront de stocker les informations extraites. 

import pandas as pd

# Lecture des fichiers
df_pontes = pd.read_csv('interim/df_pontes.csv', sep=';')
df_meteo = pd.read_csv('interim/df_meteo_commentaires_oeuf.csv', sep=';')

# On commence par nettoyer et structurer les données des df_pontes

# Je vais commencer par créer deux dataframes de pontes pour séparer les marans (qui 
# ne sont pas observées individuellement et dont les pontes sont comptées ensemble
# sauf en 2023 où il n'y avait qu'une seule poule Marans) 




df_pontes['Date'] = pd.to_datetime(df_pontes['Date'])
df_pontes['Ponte_brute'] = df_pontes['Ponte_brute'].astype(float)

# On va maintenant créer les fonctions de mapping pour les poules