import pandas as pd
import json

# Charger les données
df_2_pontes = pd.read_csv('data/intermediaire/df_2_pontes.csv', sep=';')
df_2_pontes.fillna({'Remarques': 'RAS'}, inplace=True)

df_final = df_2_pontes[['Date', 'Poule_brute','niveau_observation','Ponte', 'Etat_oeuf', 'Doute', 'Effectif', 'Remarques']]
df_final.rename(columns={'Poule_brute': 'Poule'}, inplace=True)

df_final.to_csv('data/final/pontes_format_final.csv', sep=';', index=False)