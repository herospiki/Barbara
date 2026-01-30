import pandas as pd
import re
import numpy as np

# ===========================================================================
# FONCTIONS DE TRAITEMENT DES PONTES
# ===========================================================================
df_pontes = pd.read_csv('interim/df_pontes.csv', sep=';')


def traiter_ponte_individuelle(row):
    """
    Traite une ligne de ponte pour une poule individuelle.
    Code : m = Mue, ? = Doute, c = Cassé
    """
    val = str(row['Ponte_brute']).strip().replace('\xa0', '')
    
    # Valeurs par défaut
    resultat = {
        'Ponte': 0,
        'Etat_oeuf': 'RAS',
        'Doute': False,
        'Statut_Poule': 'Présente',
        'Remarques': ''
    }
    
    # Cas NaN ou vide
    if val == 'nan' or val == '' or val == 'None':
        return pd.Series(resultat)
    
    val_lower = val.lower()

    # Gestion du Doute
    if '?' in val_lower:
        resultat['Doute'] = True
    
    # Gestion de la Mue
    if 'mue' in val_lower or '(m)' in val_lower or ' m' in val_lower:
        resultat['Statut_Poule'] = 'Mue'

    # Gestion du Décès
    if 'dcd' in val_lower:
        resultat['Statut_Poule'] = 'Décédée'
        return pd.Series(resultat)

    # Cas 1: Valeurs numériques avec annotations n(+m)
    if re.match(r'^\d+\(\+\d+\)$', val):
        match = re.match(r'^(\d+)\(\+(\d+)\)$', val)
        n = int(match.group(1))
        m = int(match.group(2))
        resultat['Ponte'] = n + m
        resultat['Remarques'] = f"{m} oeufs trouvés dehors"
        return pd.Series(resultat)
    
    # Cas 2: Valeurs avec 'x'
    if 'x' in val_lower:
        # Compter les x pour le nombre de pontes
        resultat['Ponte'] = val_lower.count('x')
        
        # État de l'œuf (Cassé)
        if 'c' in val_lower:
            resultat['Etat_oeuf'] = 'cassé'
            
        return pd.Series(resultat)
    
    # Cas 3: Valeurs numériques pures
    if val.isdigit():
        resultat['Ponte'] = int(val)
        return pd.Series(resultat)
    
    # Cas 4: Autres textes (remarques par défaut)
    if not resultat['Remarques']:
        resultat['Remarques'] = val
        
    return pd.Series(resultat)


# ===========================================================================
# TRAITEMENT DES PONTES GROUPE
# ===========================================================================

df_pontes_groupe = df_pontes[df_pontes['niveau_observation'] == 'groupe']
print(df_pontes_groupe['Ponte_brute'].unique())

def traiter_ponte_groupe(row):
    """
    Traite une ligne de ponte pour un groupe.
    Codes spécifiques : n = Nina, t = Tina, a = Albertine.
    Statut_Poule est NaN pour les groupes, l'info de Mue/Décès va en remarques.
    """
    val = str(row['Ponte_brute']).strip().replace('\xa0', '').lower()
    
    # Valeurs par défaut
    resultat = {
        'Ponte': 0,
        'Etat_oeuf': 'RAS',
        'Doute': False,
        'Statut_Poule': np.nan,
        'Remarques': ''
    }
    
    if val == 'nan' or val == '' or val == 'none' or val == '0':
        return pd.Series(resultat)

    # 1. Extraction du nombre de pontes (les 'x')
    nb_x = val.count('x')
    if nb_x > 0:
        resultat['Ponte'] = nb_x
    elif any(char.isdigit() for char in val):
        # Extraction des chiffres si pas de x (ex: '2', '2(+3)')
        if re.match(r'^\d+\(\+\d+\)$', val):
            match = re.match(r'^(\d+)\(\+(\d+)\)$', val)
            resultat['Ponte'] = int(match.group(1)) + int(match.group(2))
        else:
            nums = re.findall(r'\d+', val)
            if nums:
                resultat['Ponte'] = sum(int(n) for n in nums)

    # 2. Identification des poules et statuts
    poules_trouvees = []
    if '(n)' in val or 'x(n)' in val or '/n' in val:
        poules_trouvees.append('Nina')
    if '(t)' in val or 'x(t)' in val:
        poules_trouvees.append('Tina')
    if '(a)' in val or 'x(a)' in val:
        poules_trouvees.append('Albertine')
    
    poule_str = ", ".join(poules_trouvees) if poules_trouvees else ""

    statut_info = ""
    if 'dcd' in val:
        statut_info = "décédée"
    elif 'mue' in val or '(m)' in val or '(m?)' in val:
        statut_info = "en mue"

    # 3. Construction des Remarques
    if poule_str and statut_info:
        resultat['Remarques'] = f"{poule_str} {statut_info}"
    elif statut_info:
        resultat['Remarques'] = statut_info.capitalize()
    elif poule_str:
        resultat['Remarques'] = f"Poule(s) : {poule_str}"

    # 4. États et Doute
    if '?' in val:
        resultat['Doute'] = True
        if statut_info:
            resultat['Remarques'] += " (?)"
        
    if 'c' in val: # c = cassé
        resultat['Etat_oeuf'] = 'cassé'

    # On conserve la notation originale si vraiment complexe
    if len(val) > nb_x + val.count(' ') + val.count('x') + 2:
        suffix = f" (Notation: {val})"
        resultat['Remarques'] += suffix

    return pd.Series(resultat)


# ===========================================================================
# EXECUTION DU SCRIPT
# ===========================================================================

try:
    # 1. Chargement des données brute au format long
    df_long = pd.read_csv('interim/df_pontes.csv', sep=';')
    print(f"✅ Chargement de {len(df_long)} lignes de pontes.")

    # 2. Séparation Individuel / Groupe
    # On considère par défaut 'individuel' si non renseigné
    df_long['niveau_observation'] = df_long['niveau_observation'].fillna('individuel')
    
    mask_individuel = df_long['niveau_observation'] == 'individuel'
    mask_groupe = df_long['niveau_observation'] == 'groupe'
    
    # 3. Application des traitements
    print("🔄 Traitement des données individuelles...")
    res_indiv = df_long[mask_individuel].apply(traiter_ponte_individuelle, axis=1)
    
    print("🔄 Traitement des données groupes...")
    res_groupe = df_long[mask_groupe].apply(traiter_ponte_groupe, axis=1)
    
    # 4. Fusion des résultats avec le DataFrame original
    df_result = pd.concat([
        pd.concat([df_long[mask_individuel], res_indiv], axis=1),
        pd.concat([df_long[mask_groupe], res_groupe], axis=1)
    ]).sort_index()

    # 5. Post-traitement : Propagation du décès
    # Il faut le faire par poule
    print("🔄 Post-traitement : Propagation du décès...")
    def propager_deces(group):
        group = group.sort_values('Date')
        a_deceder = group['Statut_Poule'] == 'Décédée'
        if a_deceder.any():
            premier_deces_pos = np.where(a_deceder)[0][0]
            group.iloc[premier_deces_pos:, group.columns.get_loc('Statut_Poule')] = 'Décédée'
            group.iloc[premier_deces_pos:, group.columns.get_loc('Ponte')] = 0
        return group

    df_result = df_result.groupby('Poule_brute', group_keys=False).apply(propager_deces)

    # 6. Sauvegarde du résultat structuré
    output_meta = 'interim/df_pontes_long_traite.csv'
    df_result.to_csv(output_meta, sep=';', index=False)
    
    print(f"✅ Traitement terminé. Fichier sauvegardé : {output_meta}")
    
    # Affichage d'un aperçu
    print("\nAperçu des 10 premières lignes traitées :")
    print(df_result[['Date', 'Poule_brute', 'Ponte_brute', 'Ponte', 'Statut_Poule']].head(10))

except FileNotFoundError as e:
    print(f"❌ Erreur : Fichier non trouvé. {e}")
except Exception as e:
    import traceback
    print(f"❌ Une erreur est survenue : {e}")
    traceback.print_exc()








