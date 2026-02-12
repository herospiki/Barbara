import pandas as pd
import re
import numpy as np

# ===========================================================================
# FONCTIONS DE TRAITEMENT DES PONTES
# ===========================================================================
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
        'Effectif': 1,
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
        resultat['Remarques'] = 'Mue'

    # Gestion du Décès
    if 'dcd' in val_lower:
        resultat['Effectif'] = 0
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
        
        # État de l'œuf (Cassé) si ce n'est pas le c de dcd 
        if 'c' in val_lower and 'dcd' not in val_lower:
            resultat['Etat_oeuf'] = 'cassé'
        # Extraire le mot entre les parenthèses
        elif '(' in val_lower and ')' in val_lower:
            resultat['Etat_oeuf'] = val_lower.split('(')[1].split(')')[0]
      
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
# TRAITEMENT DES PONTES GROUPE (MARANS UNIQUEMENT)
# ===========================================================================


def traiter_ponte_groupe_marans(row):
    """
    Traite une ligne de ponte pour le groupe MARANS.
    Codes spécifiques : n = Nina, t = Tina, a = Albertine.
    Gère les effectifs variables et ajoute l'info des poules dans Remarques.
    """
    val = str(row['Ponte_brute']).strip().replace('\xa0', '').lower()
    
    # Valeurs par défaut
    resultat = {
        'Ponte': 0,
        'Etat_oeuf': 'RAS',
        'Doute': False,
        'Effectif': row.get('Effectif_theo', 3),  # Par défaut 3 Marans
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

    # 3. Construction des Remarques (TOUJOURS ajouter l'info des poules si disponible)
    remarques_parts = []
    
    if poule_str:
        remarques_parts.append(f"Poule(s) : {poule_str}")
    
    if statut_info:
        if poule_str:
            remarques_parts.append(statut_info)
        else:
            remarques_parts.append(statut_info.capitalize())
    
    resultat['Remarques'] = " - ".join(remarques_parts)

    # 4. Ajustement Effectif si décès détecté
    if statut_info == "décédée":
        resultat['Effectif'] = 2  # Passage de 3 à 2 pour les Marans

    # 5. États et Doute
    if '?' in val:
        resultat['Doute'] = True
        if resultat['Remarques']:
            resultat['Remarques'] += " (?)"
        
    if 'c' in val and 'dcd' not in val:  # c = cassé
        resultat['Etat_oeuf'] = 'cassé'

    return pd.Series(resultat)


# ===========================================================================
# EXECUTION DU SCRIPT
# ===========================================================================

def nettoyage_completion_et_structuration():
    try:
        # 1. Chargement des données brute au format long
        df_long = pd.read_csv('interim/df_1_pontes.csv', sep=';')
        print(f"✅ Chargement de {len(df_long)} lignes de pontes.")

        # 2. Préparation des masques pour le traitement
        # L'étape 1 a déjà normalisé niveau_observation (individuel, groupe)
        # et group_id (MARANS).
        
        # On s'assure que les valeurs manquantes sont gérées
        df_long['niveau_observation'] = df_long['niveau_observation'].fillna('individuel')
        
        # Convertir Date en datetime pour extraire l'année
        df_long['Date'] = pd.to_datetime(df_long['Date'])
        
        # Pré-remplissage de l'effectif théorique (utilisé par les fonctions de traitement)
        df_long['Effectif_theo'] = 1
        
        # Pour MARANS, l'effectif varie selon l'année :
        # - 2023 : 1 (Albertine seule)
        # - 2024 : 3 (Albertine + Nina + Tina)
        # - 2025 : 3 (puis 2 après décès, géré par la propagation)
        mask_marans = df_long['Poule_brute'] == 'MARANS'
        df_long.loc[mask_marans & (df_long['Date'].dt.year == 2023), 'Effectif_theo'] = 1
        df_long.loc[mask_marans & (df_long['Date'].dt.year == 2024), 'Effectif_theo'] = 3
        df_long.loc[mask_marans & (df_long['Date'].dt.year == 2025), 'Effectif_theo'] = 3
        
        mask_individuel = df_long['niveau_observation'] == 'individuel'
        mask_groupe = df_long['niveau_observation'] == 'groupe'
    
        # 3. Application des traitements
        print("🔄 Traitement des données individuelles...")
        res_indiv = df_long[mask_individuel].apply(traiter_ponte_individuelle, axis=1)
        
        print("🔄 Traitement des données groupe MARANS...")
        res_groupe = df_long[mask_groupe].apply(traiter_ponte_groupe_marans, axis=1)
        
        # 4. Fusion des résultats avec le DataFrame original
        df_result = pd.concat([
            pd.concat([df_long[mask_individuel], res_indiv], axis=1),
            pd.concat([df_long[mask_groupe], res_groupe], axis=1)
        ]).sort_index()

        # 5. Post-traitement : Propagation du décès / effectif
        print("🔄 Post-traitement : Propagation du décès et des effectifs...")
        def propager_status(group):
            # Le nom du groupe (Poule_brute) est accessible via l'attribut .name
            poule = group.name
            group = group.sort_values('Date')
            
            if group['niveau_observation'].iloc[0] == 'individuel':
                deces = group['Effectif'] == 0
                if deces.any():
                    premier_deces_pos = np.where(deces)[0][0]
                    group.iloc[premier_deces_pos:, group.columns.get_loc('Effectif')] = 0
                    group.iloc[premier_deces_pos:, group.columns.get_loc('Ponte')] = 0
            else:
                # Pour le groupe MARANS, on propage le passage de 3 à 2
                if poule == 'MARANS':
                    deces = group['Effectif'] == 2
                    if deces.any():
                        premier_deces_pos = np.where(deces)[0][0]
                        group.iloc[premier_deces_pos:, group.columns.get_loc('Effectif')] = 2
            
            # On ré-ajoute la colonne Poule_brute car include_groups=False l'exclut du traitement
            group['Poule_brute'] = poule
            return group

        df_result = df_result.groupby('Poule_brute', group_keys=False).apply(propager_status, include_groups=False)

        # Nettoyage colonnes temporaires
        if 'Effectif_theo' in df_result.columns:
            df_result = df_result.drop(columns=['Effectif_theo'])

        # 6. Sauvegarde du résultat structuré final
        # Mettre dans l'ordre les colonnes
        df_result = df_result[['Date', 'Poule_brute', 'Ponte_brute', 'Ponte', 'Effectif', 'Etat_oeuf', 'Doute', 'Remarques', 'niveau_observation', 'group_id']]
     
        output_final = 'interim/df_2_pontes.csv'
        df_result.to_csv(output_final, sep=';', index=False)
        
        print(f"✅ Traitement terminé. Fichier sauvegardé : {output_final}")
        
        # Aperçu
        print("\nAperçu des 15 premières lignes traitées :")
        cols_to_show = ['Date', 'Poule_brute', 'Ponte_brute', 'Ponte', 'Effectif', 'Remarques']
        print(df_result[cols_to_show].head(15))
        
        print("\nAperçu des lignes MARANS :")
        print(df_result[df_result['Poule_brute'] == 'MARANS'][cols_to_show].head(20))

    except FileNotFoundError as e:
        print(f"❌ Erreur : Fichier non trouvé. {e}")
    except Exception as e:
        import traceback
        print(f"❌ Une erreur est survenue : {e}")
        traceback.print_exc()

nettoyage_completion_et_structuration()
