import pandas as pd
import re
import unicodedata

df_meteo = pd.read_csv('data/intermediaire/df_2_meteo.csv', sep=';')

df_meteo['Météo'] = df_meteo['Météo'].str.lower()
df_meteo['Météo'].value_counts().reset_index().to_csv('data/intermediaire/texte_meteo_count.csv', sep=';', index=False)

MAPPING_CORRECTIF =  {
    'acalmie':'accalmie', 
     'bruine puis très beau': 'bruine/très beau', 
     'beau puis bruine' : 'beau/bruine', 
     'averses, éclaircies' : 'averses/éclaircies',
    'soleil et qq nuages' : 'soleil/qq nuages', 
    'bruine le matin': 'bruine/mitigé',
    'fortes pluie' : 'fortes pluies',
    'éclairicie':'éclaircies',
    'orage avec grésil':'orage/grésil',
}
    
def corriger_terme_meteo(expression):
    if pd.isna(expression) or expression == '' or expression is None:
        return ''
    # Nettoyage de base : minuscule, retrait des espaces
    expression_nettoyee = expression.lower().strip()
    # Essayer de mapper le terme nettoyé
    # On doit rechercher le terme dans l'expression de départ et remplacer uniquement
    # le terme en question 
    for terme, correction in MAPPING_CORRECTIF.items():
        expression_nettoyee = expression_nettoyee.replace(terme, correction)    
    return expression_nettoyee

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
   
    num_cols = min(4, df_split.shape[1]) 
    colonnes_meteo = [f'Météo_{i+1}' for i in range(num_cols)]

    # 5. Joindre ces nouvelles colonnes au DataFrame original (df)
    df_meteo = pd.concat([df_meteo, df_split.iloc[:, 0:num_cols].set_axis(colonnes_meteo, axis=1)], axis=1)
    return df_meteo

def nettoyage_et_split_meteo(df_meteo):
    df_meteo['Météo_Corrigée'] = df_meteo['Météo'].apply(corriger_terme_meteo)
    df_meteo = split_meteo(df_meteo)
    return df_meteo



# -----------------------------
# 2. DICTIONNAIRE DE MAPPING
# -----------------------------
MAPPING_METEO = {

    # ☀ BEAU
    "beau": "BEAU",
    "beau temps": "BEAU",
    "tres beau": "BEAU",
    "assez beau": "BEAU",
    "ensoleille": "BEAU",
    "soleil": "BEAU",
    "beau(ciel blanc)": "BEAU",
    "degage": "BEAU",


    # ⛅ ECLAIRCIES
    "eclaircie": "ECLAIRCIES",
    "eclaircies": "ECLAIRCIES",
    "belles eclaircies": "ECLAIRCIES",

    # ☁ COUVERT
    "couvert": "COUVERT",
    "nuageux": "COUVERT",
    "gris": "COUVERT",
    "voile": "COUVERT",
    "tres voile": "COUVERT",
    "brumeux": "COUVERT",
    "brouillard": "COUVERT",
    "brouillard epais": "COUVERT",
    "maussade": "COUVERT",

    # 🌧 PLUIE
    "pluie": "PLUIE",
    "pluie fine": "PLUIE",
    "bruine": "PLUIE",
    "averse": "PLUIE",
    "averses": "PLUIE",
    "fortes pluies": "PLUIE",
    "petite averse": "PLUIE",
    "petites averses": "PLUIE",
    "qq gouttes": "PLUIE",
    "giboulees": "PLUIE",

    # ⛈ ORAGE
    "orage": "ORAGE",
    "orages": "ORAGE",
    "orageux": "ORAGE",
    "orage fort": "ORAGE",
    "orage sec": "ORAGE",
    "orages faibles": "ORAGE",
    "averse orageuse": "ORAGE",
        # NEIGE
    "neige": "NEIGE",
    "pluie neige": "PLUIE_MIXTE",
    "grele et pluie": "PLUIE_MIXTE",
    "gresil": "PLUIE_MIXTE",
    "pluie-neige": "PLUIE_MIXTE",
    
    # 🌬 VENT
    "vent": "VENT",
    "vent violent": "VENT",
    "tempete": "VENT",
    "vent chaud": "VENT",

    # 🌡 CHALEUR
    "chaud": "CHAUD",
    "lourd": "CHAUD",
    "temps lourd": "CHAUD",
    "canicule": "CANICULE",
    "vigilance canicule": "CANICULE",

    # ❄ FROID
    "froid": "FROID",

    # ⚖ INSTABLE
    "variable": "INSTABLE",
    "mitige": "INSTABLE",
    "degradation": "INSTABLE",
    "accalmie": "INSTABLE",

    # NUAGES
    "qq nuages": "PASSAGES NUAGEUX",
}


def normalize_meteo_text(text: str) -> str:
    if text is None:
        return None
    
    # lowercase
    text = text.lower().strip()
    
    # remove accents
    text = ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )
    
    # normalize spaces
    text = re.sub(r"\s+", " ", text)
    
    return text

# Fonctions pour nettoyer et mapper 

def mapper_terme_meteo(terme):
    if pd.isna(terme) or terme == '' or terme is None or terme == '?':
        return None 
    # Nettoyage de base : minuscule, retrait des espaces
    terme_nettoye = normalize_meteo_text(terme)
    
    # Essayer de mapper le terme nettoyé
    return MAPPING_METEO.get(terme_nettoye, 'AUTRE/NON CLASSE')

# On va créer de nouvelles colonnes pour les mappings
def apply_mapping_meteo(df_meteo):
    for col in ['Météo_1', 'Météo_2', 'Météo_3', 'Météo_4']:
        if col in df_meteo.columns:
            df_meteo[col + '_Cat'] = df_meteo[col].apply(mapper_terme_meteo)
    return df_meteo
    
# Regroupement des catégories : Météo_1_Cat, Météo_2_Cat, Météo_3_Cat, Météo_4_Cat
# Sous la forme Météo_Cat : Météo_1_Cat|Météo_2_Cat|Météo_3_Cat|Météo_4_Cat 
# si la catégorie n'est pas vide. Si la colonne est vide, on ne met pas de | .
# Exemple : si on a Météo_1_Cat = BEAU, Météo_2_Cat = NUAGES, Météo_3_Cat = '', Météo_4_Cat = '',
# on aura Météo_Cat = BEAU|NUAGES

def regroupement_meteo(df_meteo):
  cols = ['Météo_1_Cat', 'Météo_2_Cat', 'Météo_3_Cat', 'Météo_4_Cat']
  # sécuriser colonnes manquantes
  for col in cols:
    if col not in df_meteo.columns:
      df_meteo[col] = ''
    
    # normaliser NaN -> '' + strip
    df_meteo[cols] = df_meteo[cols].fillna('').apply(lambda s: s.astype(str).str.strip())
   
   
    # concat seulement valeurs non vides et en ordonnant les valeurs
    df_meteo['Météo_Cat'] = df_meteo[cols].apply(
        lambda row: ' | '.join(sorted([v for v in row if v != ''])),
        axis=1
    )
    
    return df_meteo



new_df_meteo = nettoyage_et_split_meteo(df_meteo)
meteo_categories_df = apply_mapping_meteo(new_df_meteo)
meteo_categories_df = regroupement_meteo(meteo_categories_df)
meteo_categories_df.to_csv('data/intermediaire/df_3_meteo.csv', sep=';', index=False) 
