import pandas as pd
marans_df = pd.read_csv('interim/df_2_pontes_marans.csv', sep=';')
print(marans_df.head())

hors_marans_df = pd.read_csv('interim/df_2_pontes_hors_marans.csv', sep=';')
print(hors_marans_df.head())

# Pour les poules Marans, on a 3 poules : Albertine, Nina et Tina, et des informations
# de groupe. Pour faciliter le traitement, on ne va considérer qu'une seule
# groupe dont l'effectif varie de 1 à 3. 

# Pour 2023 : 1 Marans (Albertine)
# Pour 2024 : 2 Marans (Nina et Tina) + 1 Marans (Albertine) = 3 Marans (MARANS_TOTAL)
# Pour 2025 : 3 Marans (MARANS_TOTAL)

# On va réserver dans un autre dataframe
# les données Albertine, Nina et Tina pour les analyses futures (ainsi que le groupe 
# NINA_TINA)

def extract_marans_individuel(marans_df):
    df_result = marans_df[marans_df['Poule_brute'].isin(['Albertine', 'Nina', 'Tina'])]
    return df_result

# On va remplacer Albertine par MARANS_TOTAL pour 2023 uniquement car elle est déjà
# comprise dans le total pour les autres années

def combine_marans_dataframes(hors_marans_df, marans_df):
    # Renommage Albertine en MARANS_TOTAL pour 2023 uniquement
    marans_df['Date'] = pd.to_datetime(marans_df['Date'], format='%Y-%m-%d')
    mask = ((marans_df["Date"].dt.year == 2023) & (marans_df["Poule_brute"] == "Albertine"))
    marans_df.loc[mask, "Remarques"] = 'Poule(s) : Albertine' 
    marans_df.loc[mask, "Poule_brute"] = "MARANS_TOTAL"
    print(marans_df.head(15))
    groupe_marans_df = marans_df[marans_df['Poule_brute'] == 'MARANS_TOTAL']
    print(groupe_marans_df.shape)
    print(groupe_marans_df.head(15))
    df_result = pd.concat([hors_marans_df, groupe_marans_df])
    print(df_result.shape)
    print(df_result.head(15)    )
    mask2 = (df_result['Poule_brute'] == 'MARANS_TOTAL')
    df_result.loc[mask2, 'Poule_brute'] = 'MARANS'   
    return df_result

df_marans_combine = combine_marans_dataframes(hors_marans_df, marans_df)

df_marans_combine['Date'] = pd.to_datetime(df_marans_combine['Date'], format='%Y-%m-%d')
df_marans_combine = df_marans_combine.sort_values(by='Date', ascending=True)
print(df_marans_combine.head(15))
df_marans_combine.to_csv('final/fichier_final_pontes.csv', sep=';', index=False)
