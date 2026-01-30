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

# Pivot des colonnes Poules pour aboutir à un format plus exploitable 
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

def selection_meteo_commentaires(df, poules):
    # Utiliser ~isin pour exclure les colonnes qui sont des poules
    colonnes_a_garder = ['Date'] + [col for col in df.columns if col not in poules]
    return df[colonnes_a_garder]

# Premiers choix de conservation de certaines colonnes 
# On conserve les colonnes communes aux 3 années ainsi que la colonne Humidité
# même si elle n'apparait pas en 2023 car elle a une valeur métier : l'humidité
# rend la chaleur beaucoup plus difficile à supporter et cela peut affecter les 
# animaux. 
# On va conserver aussi la nouvelle colonne "oeuf trouvé/date de la trouvaille"
# qui est apparue en 2025 et voir si on peut l'utiliser plus tard pour 
# améliorer la qualité de nos données.

def selectionner_colonnes(df):
    colonnes_cibles = ['Date', 'Météo', 'Pluie(mm)', 'Humidité', 'Commentaires', 'T°C (12h-15h)', 'œuf trouvé/date de la trouvaille']
    # On ne garde que les colonnes présentes dans la liste des colonnes cibles
    existantes = [col for col in colonnes_cibles if col in df.columns]
    return df[existantes]

# Application
df_meteo_2023 = selectionner_colonnes(df_2023)
df_meteo_2024 = selectionner_colonnes(df_2024)
df_meteo_2025 = selectionner_colonnes(df_2025)

print("\nColonnes conservées pour la météo 2023 :", df_meteo_2023.columns.tolist())
print("\nColonnes conservées pour la météo 2024 :", df_meteo_2024.columns.tolist())
print("\nColonnes conservées pour la météo 2025 :", df_meteo_2025.columns.tolist())

# On concatène les df_meteo en un seul dataframe
df_meteo = pd.concat([df_meteo_2023, df_meteo_2024, df_meteo_2025], axis=0)
df_meteo.sort_values(by='Date', inplace=True)

# On sauvegarde les df_pontes et df_meteo dans le répertoire interim
df_pontes.to_csv('interim/df_pontes.csv', index=False, encoding='utf-8-sig', sep=';')
df_meteo.to_csv('interim/df_meteo_commentaires_oeuf.csv', index=False, encoding='utf-8-sig', sep=';')
