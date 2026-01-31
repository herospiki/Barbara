import pandas as pd
import re

df_meteo = pd.read_csv('interim/df_meteo_clean.csv', sep=';')
print(df_meteo.head())

df_meteo['Météo'] = df_meteo['Météo'].str.lower()
df_meteo['Météo'].value_counts().reset_index().to_csv('interim/texte_meteo_count.csv', sep=';', index=False)

MAPPING_CORRECTIF =  {
    'acalmie':'accalmie', 
     'bruine puis très beau': 'bruine/très beau', 
     'beau puis bruine' : 'beau/bruine', 
     'averses, éclaircies' : 'averses/éclaircies',
    'soleil et qq nuages' : 'soleil/qq nuages', 
    'bruine le matin': 'bruine/mitigé',
    'fortes pluie' : 'fortes pluies',
    'éclairicie':'éclaircies'
}
    
def corriger_terme_meteo(terme):
    if pd.isna(terme) or terme == '' or terme is None:
        return ''
    
    # Nettoyage de base : minuscule, retrait des espaces
    terme_nettoye = terme.lower().strip()
    
    # Essayer de mapper le terme nettoyé
    return MAPPING_CORRECTIF.get(terme_nettoye,terme)

def split_meteo(df_meteo):
    # 1. Remplacer les NaN par une chaîne vide pour éviter les erreurs lors du .str.split()
    #    et convertir tout en chaîne de caractères
    df_meteo['Météo_Clean'] = df_meteo['Météo_Corrigée'].astype(str).replace('nan', '').str.strip()

    # --- Séparation ---
    # 2. Utiliser str.split() pour séparer la colonne
    #    Le 'expand=True' transforme la série en DataFrame de nouvelles colonnes
    df_split = df_meteo['Météo_Clean'].str.split(pat='/', expand=True)

    # 3. Optionnel : Nettoyer les espaces blancs restants dans les nouvelles colonnes
    for col in df_split.columns:
        if df_split[col].dtype == 'object':
            df_split[col] = df_split[col].str.strip()

    # --- Intégration ---
    # 4. Renommer les colonnes de manière explicite (Météo_1, Météo_2, etc.)
    #    On prend le nombre maximum de composants trouvé + 1 (ici, 4 colonnes max par sécurité)
    num_cols = min(4, df_split.shape[1]) # Limite à 4 colonnes ou moins si moins de séparateurs sont trouvés
    colonnes_meteo = [f'Météo_{i+1}' for i in range(num_cols)]

    # 5. Joindre ces nouvelles colonnes au DataFrame original (df)
    df_meteo = pd.concat([df_meteo, df_split.iloc[:, 0:num_cols].set_axis(colonnes_meteo, axis=1)], axis=1)
    return df_meteo

def nettoyage_et_split_meteo(df_meteo):
    df_meteo['Météo_Corrigée'] = df_meteo['Météo'].apply(corriger_terme_meteo)
    df_meteo = split_meteo(df_meteo)
    return df_meteo

new_df_meteo = nettoyage_et_split_meteo(df_meteo)
new_df_meteo.to_csv('interim/df_meteo_clean_split.csv', sep=';', index=False)


# Mapping des termes détaillés (Clé) vers la catégorie
MAPPING_METEO = {
    # Catégorie BEAU
    'beau': 'BEAU', 'soleil': 'BEAU', 'ensoleillé': 'BEAU', 'dégagé': 'BEAU', 
    'beau temps': 'BEAU', 'assez beau': 'BEAU', 'très beau' :'BEAU',
    
    # Catégorie PLUIE
    'pluie':'PLUIE', 'bruine': 'PLUIE','averse': 'PLUIE', 'averses': 'PLUIE', 'giboulées': 'PLUIE', 
    'qq gouttes': 'PLUIE', 'pluie fine': 'PLUIE', 'fortes pluies':'PLUIE',
    
    # Catégorie VENT
    'vent': 'VENT', 'tempête': 'VENT', 'vent violent': 'VENT', 'vent chaud': 'VENT',
    
    # Catégorie COUVERT/GRIS
    'couvert': 'COUVERT', 'nuageux': 'COUVERT', 'gris': 'COUVERT', 'voilé': 'COUVERT', 
    'brumeux': 'COUVERT', 'brouillard': 'COUVERT', 'nuageux/': 'COUVERT', 'brouillard épais': 'COUVERT',
    'très voilé' :'COUVERT',
    
    # Catégorie CHALEUR/FROID
    'froid': 'FROID', 'chaud': 'CHAUD', 'lourd': 'CHAUD', 'temps lourd':' CHAUD',
    'canicule': 'CANICULE', 'vigilance canicule': 'CANICULE',
    
    # Catégorie PHENOMENE SPECIFIQUE
    'neige': 'NEIGE', 'orage': 'ORAGE', 'orageux': 'ORAGE', 'orages': 'ORAGE',
    'orage fort': 'ORAGE',
    
    # Catégorie ECLAIRCIE
    'éclaircie': 'ECLAIRCIES', 'éclaircies': 'ECLAIRCIES', 'belles éclaircies':'ECLAIRCIES',

    # Catégorie NUAGES

    'qq nuages' : 'NUAGES',
    
    # Catégorie MITIGE / TRANSITION
    'mitigé': 'MITIGE', 'idem': 'MITIGE',
    
    # Autres
    'absente': 'NON ENREGISTRE',
}
    

# Fonction pour nettoyer et mapper (pour les cas complexes non couverts par le split)
def mapper_terme_meteo(terme):
    if pd.isna(terme) or terme == '' or terme is None or terme == '?':
        return 'NON RENSEIGNE' 
    # Nettoyage de base : minuscule, retrait des espaces
    terme_nettoye = terme.lower().strip()
    
    # Essayer de mapper le terme nettoyé
    return MAPPING_METEO.get(terme_nettoye, 'AUTRE/NON CLASSE')

    
    
    