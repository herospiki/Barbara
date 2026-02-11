import pandas as pd
import json

# Charger les données
df_2_pontes = pd.read_csv('Interim/df_2_pontes.csv', sep=';')

print(df_2_pontes.head())


df_2_pontes.fillna({'Remarques': 'RAS'}, inplace=True)
print(df_2_pontes.head())

df_final = df_2_pontes[['Date', 'Poule_brute','niveau_observation','group_id','Ponte', 'Etat_oeuf', 'Doute', 'Effectif', 'Remarques']]
df_final.rename(columns={'Poule_brute': 'Poule'}, inplace=True)
print(df_final.head())

df_final.to_csv('final/pontes_final.csv', sep=';', index=False)