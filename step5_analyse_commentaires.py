import pandas as pd
import os
import re


def nettoyer_commentaires(df_commentaires):
    # Séparer les commentaires multiples (ceux contenant un /)
    # On évite de couper les dates (ex: 22/02) en ne coupant que si le slash n'est pas entouré de chiffres
    df_commentaires['Commentaires_clean'] = df_commentaires['Commentaires'].str.split(r'(?<!\d)/(?!\d)')
    df_commentaires = df_commentaires.explode('Commentaires_clean')
    df_commentaires['Commentaires_clean'] = df_commentaires['Commentaires_clean'].str.strip()
    df_commentaires = df_commentaires[df_commentaires['Commentaires_clean'] != ""] # Supprimer les segments vides éventuels
    return df_commentaires

# Liste exhaustive des poules pour détection
liste_poules = [
    'Joséphine', 'Albertine', 'Augustine', 'Cunégonde', 'Pioupioute', 
    'Valérie', 'Rémiel', 'Saquiel', 'Tina', 'Nina', 'Marans'
]

# Définition des catégories et mots-clés prioritaires
# L'ordre dans le dictionnaire définit la priorité (Mutuellement exclusif)
def definition_categories():
    categories_prioritaires = {
    'Météo / Environnement': [
        r'°c', r'h%', r'gel', r'neige', r'tempête', r'orage', r'froid', r'canicule', r'chaleur', 
        r'frais', r'chaud', r'humide', r'humidité', r'inondation', r'temps', r'ciel',
        r'vent', r'vigilance', r'alerte', r'soleil', r'pluie', r'mm',
        r'brouillard', r'grêle', r'arcus', r'sahara', r'fumée', r'gouttes',r'T°ext'
    ],
    'Santé / Soins': [
        r'malade', r'véto', r'dcd', r'mort', r'soin', r'vitamine', r'vit c', r'vitc', r'antibio', 
        r'vermifuge', r'avipar', r'estropiée', r'blessée', r'abcès', r'exzolt', 
        r'avicoryl', r'doxycycline', r'doxycyline', r'amirudène', r'lentypou', r'atipou', r'avipou',
        r'gascodrène', r'oligoélément', r'calcium', r'mue', r'tousse', r'rhume',
        r'poux rouges', r'envt', r'fatiguée', r'enrhumée', r'décédée', r'décès', r'traitement',
        r'c\+gasco', r'gasco'
    ],
    'Alimentation': [
        r'aliment', r'blé', r'lait', r'pain', r'pâtée', r'maïs'
    ],
    'Anomalies Œufs': [
        r'cassé', r'mou', r'petit', r'micro', r'coquille', r'minuscule', r'géant', 
        r'tordu', r'rugueux', r'sans coquille', r'fibrine', r'0 œuf', r'0 oeuf', r'anomalie'
    ],
    'Localisation Œufs': [
        r'trouvé', r'jardin', r'ailleurs', r'n\'importe où', r'place'
    ],
    'Installation / Technique': [
        r'nettoyage', r'thermomètre', r'paille', r'volière', r'voile d\'ombrage',
        r'voile'
    ],
    'Suivi de Ponte / Observation': [
        r'œuf', r'oeuf', r'pondu', r'ponte', r'date de ponte',r'pond'
    ],
    'Vie du Poulailler / Divers': [
        r'absente', r'départ', r'arrivée', r'retour', r'nouveau', r'poulailler',r'ancienne', r'morts', 
        r'idem',r'pique', r'couve', r'cloque', r'bagarre', r'picage', r'attaque', r'boite', r'coquine',
        r'épervier', r'rapace', r'coq', r'dark vador', r'vador'
    ]}
    return categories_prioritaires

def identifier_poules(texte):
    texte_lower = str(texte).lower()
    trouvees = []
    for p in liste_poules:
        # On utilise des regex pour éviter de trouver 'Tina' dans 'Matinal' par exemple
        if re.search(r'\b' + p.lower() + r'\b', texte_lower):
            trouvees.append(p)
    return ", ".join(trouvees) if trouvees else "Aucune"

def categoriser_unique(texte):
    categories_prioritaires = definition_categories()
    texte = str(texte).lower()
    # On cherche la première catégorie qui matche (Ordre de priorité respecté)
    for cat, keywords in categories_prioritaires.items():
        for kw in keywords:
            if re.search(kw, texte):
                return cat
    return "Autre"

def print_to_file(file_path,text):
 
  # 1. Créer le dossier s'il n'existe pas pour éviter l'erreur
    os.makedirs('interim', exist_ok=True)

    
    
    # 2. Utiliser le mode 'a' (append) directement. 
    # Si le fichier n'existe pas, 'a' le crée comme 'w'. Pas besoin de IF.
    with open(file_path, 'a', encoding='utf-8') as f:
        # Convertir systématiquement en string pour éviter les crashs
        f.write(str(text) + "\n")

def stats_cat(df_commentaires):
    file_path = 'interim/analyse_detaillee_commentaires.txt'
    # Analyse par catégorie 
    stats_cat = df_commentaires['Catégorie'].str.split(', ').explode().value_counts()
    print_to_file(file_path,"\n--- Statistiques par Catégorie de Commentaires ---")
    print_to_file(file_path,stats_cat.to_string())
    categories_prioritaires = definition_categories()
    print_to_file(file_path,"\n--- Exemples par Catégorie ---")
    for cat in categories_prioritaires.keys():
        print_to_file(file_path,f"\n[{cat.upper()}]")
        exemples = df_commentaires[df_commentaires['Catégorie'] == cat]['Commentaires_clean'].unique()[:5]
        for ex in exemples:
            print_to_file(file_path,f" - {ex}")

def all_steps():
    # Charger les données
    df_commentaires = pd.read_csv('interim/df_1_commentaires.csv', sep=';')
    df_commentaires = nettoyer_commentaires(df_commentaires)
    df_commentaires['Catégorie'] = df_commentaires['Commentaires_clean'].apply(categoriser_unique)
    df_commentaires['Poules_Citées'] = df_commentaires['Commentaires_clean'].apply(identifier_poules)
    
    stats_cat(df_commentaires)

    df_commentaires.to_csv('interim/tableau_commentaires.csv', index=False, encoding='utf-8-sig', sep=';')
    print("\nLe tableau détaillé a été exporté dans 'tableau_commentaires.csv'")

all_steps()