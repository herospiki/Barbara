import pandas as pd
import re

# Charger les données
df_2023 = pd.read_excel('ponte_2023.xlsx')
df_2024 = pd.read_excel('ponte_2024.xlsx')
df_2025 = pd.read_excel('ponte_2025.xlsx')

def extraire_commentaires(df, annee):
    # La colonne peut s'appeler 'Commentaires' ou 'commentaires' (vu dans data_treatment_v3.py)
    col_name = 'Commentaires' if 'Commentaires' in df.columns else 'commentaires' if 'commentaires' in df.columns else None
    
    if col_name is None:
        return pd.DataFrame()
        
    comments = df[['Date', col_name]].dropna()
    comments.columns = ['Date', 'Texte']
    comments['Année'] = annee
    return comments

all_comments = pd.concat([
    extraire_commentaires(df_2023, 2023),
    extraire_commentaires(df_2024, 2024),
    extraire_commentaires(df_2025, 2025)
], ignore_index=True)

# Séparer les commentaires multiples (ceux contenant un /)
# On évite de couper les dates (ex: 22/02) en ne coupant que si le slash n'est pas entouré de chiffres
all_comments['Texte'] = all_comments['Texte'].str.split(r'(?<!\d)/(?!\d)')
all_comments = all_comments.explode('Texte')
all_comments['Texte'] = all_comments['Texte'].str.strip()
all_comments = all_comments[all_comments['Texte'] != ""] # Supprimer les segments vides éventuels

# Liste exhaustive des poules pour détection
liste_poules = [
    'Joséphine', 'Albertine', 'Augustine', 'Cunégonde', 'Pioupioute', 
    'Valérie', 'Rémiel', 'Saquiel', 'Tina', 'Nina', 'Marans', 'Shrek'
]

# Définition des catégories et mots-clés prioritaires
# L'ordre dans le dictionnaire définit la priorité (Mutuellement exclusif)
categories_prioritaires = {
    'Météo / Environnement': [
        r'°c', r'h%', r'gel', r'neige', r'tempête', r'orage', r'froid', r'canicule', r'chaleur', 
        r'frais', r'chaud', r'humide', r'humidité', r'inondation', r'temps', r'ciel',
        r'vent', r'vigilance', r'alerte', r'soleil', r'pluie', r'mm',
        r'brouillard', r'grêle', r'arcus', r'sahara', r'fumée', r'gouttes', r't°p'
    ],
    'Santé / Soins': [
        r'malade', r'véto', r'dcd', r'mort', r'soin', r'vitamine', r'vit c', r'vitc', r'antibio', 
        r'vermifuge', r'avipar', r'estropiée', r'blessée', r'abcès', r'exzolt', 
        r'avicoryl', r'doxycycline', r'doxycyline', r'amirudène', r'lentypou', r'atipou', r'avipou',
        r'gascodrène', r'oligoélément', r'calcium', r'mue', r'tousse', r'rhume',
        r'poux rouges', r'envt', r'fatiguée', r'enrhumée', r'décédée', r'décès', r'traitement',
        r'c\+gasco', r'gasco'
    ],
    'Anomalies Œufs': [
        r'cassé', r'mou', r'petit', r'micro', r'coquille', r'minuscule', r'géant', 
        r'tordu', r'rugueux', r'sans coquille', r'fibrine', r'0 œuf', r'0 oeuf', r'anomalie'
    ],
    'Localisation Œufs': [
        r'trouvé', r'jardin', r'ailleurs', r'n\'importe où', r'place'
    ],
    'Alimentation': [
        r'aliment', r'blé', r'lait', r'pain', r'pâtée'
    ],
    'Comportement': [
        r'pique', r'couve', r'cloque', r'bagarre', r'picage', r'attaque', r'boite', r'coquine',
        r'épervier', r'rapace', r'coq', r'dark vador', r'vador'
    ],
    'Installation / Technique': [
        r'nettoyage', r'thermomètre', r'paille', r'pond', r'poulailler', r'volière', r'voile d\'ombrage',
        r'voile', r'marans'
    ],
    'Suivi de Ponte / Observation': [
        r'œuf', r'oeuf', r'pondu', r'ponte', r'date de ponte'
    ],
    'Vie du Poulailler / Divers': [
        r'absente', r'départ', r'arrivée', r'retour', r'nouveau', r'ancienne', r'morts', r'idem'
    ]
}

def identifier_poules(texte):
    texte_lower = str(texte).lower()
    trouvees = []
    for p in liste_poules:
        # On utilise des regex pour éviter de trouver 'Tina' dans 'Matinal' par exemple
        if re.search(r'\b' + p.lower() + r'\b', texte_lower):
            trouvees.append(p)
    return ", ".join(trouvees) if trouvees else "Aucune"

def categoriser_unique(texte):
    texte = str(texte).lower()
    # On cherche la première catégorie qui matche (Ordre de priorité respecté)
    for cat, keywords in categories_prioritaires.items():
        for kw in keywords:
            if re.search(kw, texte):
                return cat
    return "Autre"

all_comments['Catégorie'] = all_comments['Texte'].apply(categoriser_unique)
all_comments['Poules_Cités'] = all_comments['Texte'].apply(identifier_poules)

# Analyse par catégorie
stats_cat = all_comments['Catégorie'].str.split(', ').explode().value_counts()

print("\n--- Statistiques par Catégorie de Commentaires ---")
print(stats_cat)

print("\n--- Exemples par Catégorie ---")
for cat in categories_prioritaires.keys():
    print(f"\n[{cat.upper()}]")
    exemples = all_comments[all_comments['Catégorie'] == cat]['Texte'].unique()[:5]
    for ex in exemples:
        print(f" - {ex}")

# Sauvegarder l'analyse détaillée
all_comments.to_csv('analyse_detaillee_commentaires.csv', index=False, encoding='utf-8-sig', sep=';')
print("\nL'analyse détaillée a été exportée dans 'analyse_detaillee_commentaires.csv'")
