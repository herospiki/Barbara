import pandas as pd
import os

meteo_df = pd.read_csv('interim/df_3_meteo.csv', sep=';', encoding='utf-8')
pontes_df = pd.read_csv('final/pontes_final.csv', sep=';', encoding='utf-8')

# Vérifier d'abord l'unicité des dates dans le fichier meteo

meteo_df['Date'] = pd.to_datetime(meteo_df['Date'])
pontes_df['Date'] = pd.to_datetime(pontes_df['Date'])
print(meteo_df['Date'].duplicated().sum())

# Calculer une vue "combinée" du dataframe des pontes en simplifiant le format :
# 1 date, 1 nombre d'oeufs, 1 effectif (nombre de poules)
# Il faut regrouper par date et faire la somme des effectifs et des pontes. 

pontes_agg_df = pontes_df.groupby(['Date']).agg({'Effectif': 'sum', 'Ponte': 'sum'}).reset_index()

print(pontes_agg_df.head())

# Maintenant on peut faire la jointure entre les deux dataframes sur la 
# colonne Date

pontes_meteo_df = pd.merge(pontes_agg_df, meteo_df, on='Date', how='left')

print(pontes_meteo_df.head())

pontes_meteo_df = pontes_meteo_df.rename(columns={'Effectif': 'Effectif_poules', 'Ponte': 'Nombre_pontes'})

pontes_meteo_df.to_csv('final/pontes_meteo.csv', sep=';', encoding='utf-8', index=False)

