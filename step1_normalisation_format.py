import pandas as pd

# Lecture des fichiers
df_2023 = pd.read_excel('data/ponte_2023.xlsx')
df_2024 = pd.read_excel('data/ponte_2024.xlsx')
df_2025 = pd.read_excel('data/ponte_2025.xlsx')

# Renommer la colonne de température et la colonne pluie pour 
# qu'elle soit cohérente avec les autres années ainsi que la colonne 3 Marans
# en Marans (il est connu qu'elles sont trois : Albertine, Tina, et Nina)

def renommer_colonnes(df):
    df = df.rename(columns={'T°C (12-15h)': 'T°C (12h-15h)'})
    df = df.rename(columns={'Pluie': 'Pluie(mm)'})
    df = df.rename(columns={'3 Marans': 'Marans'})
    return df

# On applique la fonction renommer_colonnes à chaque dataframe
df_2023 = renommer_colonnes(df_2023)
df_2024 = renommer_colonnes(df_2024)
df_2025 = renommer_colonnes(df_2025)

# Rappel des noms des poules ou groupes de poules

poules_2023 = ['Joséphine', 'Albertine', 'Augustine', 'Cunégonde', 'Pioupioute', 'Valérie', 'Rémiel', 'Saquiel']
poules_2024 = ['Joséphine', 'Albertine', 'Cunégonde', 'Valérie', 'Pioupioute', 'Rémiel', 'Nina et Tina', 'Marans', 'Nina', 'Tina']
poules_2025 = ['Joséphine', 'Cunégonde', 'Valérie', 'Pioupioute', 'Rémiel', 'Marans']

poules = set(poules_2023).union(set(poules_2024)).union(set(poules_2025))
print(poules)

# Définition des groupes de poules
poules_individuelles_hors_marans = ['Joséphine', 'Augustine', 'Cunégonde', 'Valérie','Pioupioute', 'Rémiel', 'Saquiel']
poules_marans_individuelles = ['Albertine', 'Tina', 'Nina']
poules_marans_groupes = ['Marans', 'Nina et Tina']

# Extraire les colonnes qui ne sont pas les poules
autres_colonnes_2023 = df_2023.columns.difference(poules_2023)
autres_colonnes_2024 = df_2024.columns.difference(poules_2024)
autres_colonnes_2025 = df_2025.columns.difference(poules_2025)
autres_colonnes = set(autres_colonnes_2023).intersection(set(autres_colonnes_2024)).intersection(set(autres_colonnes_2025))
print(autres_colonnes)

# Auditer de nouveau les colonnes et stocker dans le répertoire interim
from step0_audit_donnees import comparer_structures

comp = comparer_structures(df_2023[autres_colonnes_2023], \
df_2024[autres_colonnes_2024], \
df_2025[autres_colonnes_2025])
comp.to_csv('interim/audit_autres_colonnes.csv', index=False, encoding='utf-8-sig', sep=';')


# Séparation des données en plusieurs dataframes :
# 1 - Les poules (pontes)
# 2 - Les autres données météo, températures, humidité, commentaires, oeuf trouvé/date de la trouvaille

autres_colonnes = ['Date', 'Météo', 'Pluie(mm)','Humidité', 'Commentaires','T°C (12h-15h)', 'œuf trouvé/date de la trouvaille']


# Dépivotage des colonnes Poules pour aboutir à un format plus exploitable 
# On garde Date, Poule_brute, Ponte_brute (notation d'origine)

def format_long_poules(df, poules):
    """
    Transforme le DataFrame en format long :
    - Date
    - Poule_brute (nom de la poule)
    - Ponte_brute (valeur de la notation)
    """
    # Sélectionner Date + colonnes des poules
    df_filtre = df[['Date'] + [col for col in df.columns if col in poules]]
    
    # Transformer en format long
    df_long = df_filtre.melt(id_vars='Date', var_name='Poule_brute', value_name='Ponte_brute')
    
    return df_long

# Concaténer les df_long en un seul dataframe
def concat_poules(list_df_long):
    df_pontes = pd.concat(list_df_long, axis=0)
    return df_pontes

# Fonction globale qui va pivoter chaque dataframe (df_2023, df_2024, df_2025) 
# et concaténer les df_pivot en un seul dataframe

def pivoter_et_concatener_poules(df_2023, df_2024, df_2025, poules):
    df_long_2023 = format_long_poules(df_2023, poules)
    df_long_2024 = format_long_poules(df_2024, poules)
    df_long_2025 = format_long_poules(df_2025, poules)
    df_pontes = concat_poules([df_long_2023, df_long_2024, df_long_2025])
    return df_pontes

df_pontes = pivoter_et_concatener_poules(df_2023, df_2024, df_2025, poules)
df_pontes.sort_values(by='Date', inplace=True)

# ===========================================================================
# NOUVEAU : Regroupement simplifié des Marans dès le début
# ===========================================================================

def regrouper_marans_simplifie(df):
    """
    Regroupe toutes les poules Marans (Albertine, Nina, Tina, Nina et Tina, Marans)
    en un seul groupe 'MARANS' dès le début.
    
    Gère l'effectif variable selon l'année :
    - 2023 : effectif = 1 (Albertine seule)
    - 2024 : effectif = 3 (Albertine + Nina + Tina)
    - 2025 : effectif = 3 (puis 2 après décès)
    
    Sauvegarde les données individuelles dans un fichier séparé pour analyses futures.
    """
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'])
    
    # 1. Sauvegarder les données individuelles Marans + sous-groupe Nina et Tina
    poules_marans_a_conserver = ['Albertine', 'Nina', 'Tina', 'Nina et Tina']
    df_marans_individuels = df[df['Poule_brute'].isin(poules_marans_a_conserver)].copy()
    df_marans_individuels.to_csv('interim/df_1_marans_individuels.csv', index=False, encoding='utf-8-sig', sep=';')
    print(f"✅ Données individuelles Marans sauvegardées : {len(df_marans_individuels)} lignes")
    
    # 2. Identifier et traiter les lignes Marans
    marans_a_regrouper = ['Albertine', 'Nina', 'Tina', 'Nina et Tina', 'Marans']
    
    # Séparer les données Marans et non-Marans
    df_marans = df[df['Poule_brute'].isin(marans_a_regrouper)].copy()
    df_autres = df[~df['Poule_brute'].isin(marans_a_regrouper)].copy()
    
    # 3. Pour chaque date, fusionner les lignes Marans en une seule
    # On prend la première valeur non-NaN pour Ponte_brute
    def fusionner_marans_par_date(group):
        # Prendre la première valeur non-NaN
        ponte_brute = group['Ponte_brute'].dropna().iloc[0] if not group['Ponte_brute'].dropna().empty else None
        date = group.name  # Le nom du groupe est la Date
        return pd.Series({
            'Date': date,
            'Poule_brute': 'MARANS',
            'Ponte_brute': ponte_brute
        })
    
    df_marans_fusionne = df_marans.groupby('Date', group_keys=False).apply(fusionner_marans_par_date, include_groups=False)
    df_marans_fusionne = df_marans_fusionne.reset_index(drop=True)
    
    # 4. Ajouter les colonnes niveau_observation et group_id
    df_marans_fusionne['niveau_observation'] = 'groupe'
    df_marans_fusionne['group_id'] = 'MARANS'
    
    df_autres['niveau_observation'] = 'individuel'
    df_autres['group_id'] = None
    
    # 5. Recombiner les dataframes
    df_final = pd.concat([df_autres, df_marans_fusionne], axis=0)
    df_final = df_final.sort_values(by='Date').reset_index(drop=True)
    
    return df_final

df_pontes = regrouper_marans_simplifie(df_pontes)


# Premiers choix de conservation de certaines colonnes 
# On conserve les colonnes communes aux 3 années ainsi que la colonne Humidité
# même si elle n'apparait pas en 2023 car elle a une valeur métier : l'humidité
# rend la chaleur beaucoup plus difficile à supporter et cela peut affecter les 
# animaux. 
# On va séparer les colonnes météo des colonnes commentaires
# On va conserver aussi la nouvelle colonne "oeuf trouvé/date de la trouvaille"
# qui est apparue en 2025 et voir si on peut l'utiliser plus tard pour 
# améliorer la qualité de nos données.

colonnes_meteo = ['Date', 'Météo', 'Pluie(mm)', 'Humidité',  'T°C (12h-15h)',]
colonnes_commentaires = ['Date', 'Commentaires','œuf trouvé/date de la trouvaille']

def selectionner_colonnes_meteo(df):
    # On ne garde que les colonnes présentes dans la liste des colonnes cibles
    existantes = [col for col in colonnes_meteo if col in df.columns]
    return df[existantes]

def selectionner_colonnes_commentaires(df):
    # On ne garde que les colonnes présentes dans la liste des colonnes cibles
    existantes = [col for col in colonnes_commentaires if col in df.columns]
    return df[existantes]

# Application
df_meteo_2023 = selectionner_colonnes_meteo(df_2023)
df_meteo_2024 = selectionner_colonnes_meteo(df_2024)
df_meteo_2025 = selectionner_colonnes_meteo(df_2025)

print("\nColonnes conservées pour la météo 2023 :", df_meteo_2023.columns.tolist())
print("\nColonnes conservées pour la météo 2024 :", df_meteo_2024.columns.tolist())
print("\nColonnes conservées pour la météo 2025 :", df_meteo_2025.columns.tolist())

    # On concatène les df_meteo en un seul dataframe
df_meteo = pd.concat([df_meteo_2023, df_meteo_2024, df_meteo_2025], axis=0)
df_meteo.sort_values(by='Date', inplace=True)

df_commentaires_2023 = selectionner_colonnes_commentaires(df_2023)
df_commentaires_2024 = selectionner_colonnes_commentaires(df_2024)
df_commentaires_2025 = selectionner_colonnes_commentaires(df_2025)

# On concatène les df_commentaires en un seul dataframe
df_commentaires = pd.concat([df_commentaires_2023, df_commentaires_2024, df_commentaires_2025], axis=0)
df_commentaires.sort_values(by='Date', inplace=True)

# On sauvegarde les df_pontes et df_meteo dans le répertoire interim
df_pontes.to_csv('interim/df_1_pontes.csv', index=False, encoding='utf-8-sig', sep=';')
df_meteo.to_csv('interim/df_1_meteo.csv', index=False, encoding='utf-8-sig', sep=';')
df_commentaires.to_csv('interim/df_1_commentaires.csv', index=False, encoding='utf-8-sig', sep=';')

print(f"\n✅ Fichiers sauvegardés :")
print(f"  - df_1_pontes.csv : {len(df_pontes)} lignes")
print(f"  - df_1_meteo.csv : {len(df_meteo)} lignes")
print(f"  - df_1_commentaires.csv : {len(df_commentaires)} lignes")
