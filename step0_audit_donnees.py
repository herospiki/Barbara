import pandas as pd
import numpy as np

def analyser_colonnes(df):
    """
    Retourne un résumé statistique de toutes les colonnes d'un DataFrame.
    """
    resume = []
    print("Analyse des colonnes...")
    for col in df.columns:
        # Calcul des statistiques de base
        dtype = df[col].dtype
        non_null = df[col].count()
        null_count = df[col].isna().sum()
        null_pct = (null_count / len(df)) * 100
        nunique = df[col].nunique()
        
        # Récupération des valeurs les plus fréquentes (Top 3)
        top_values = df[col].value_counts().head(3).to_dict()
        top_str = ", ".join([f"'{k}': {v}" for k, v in top_values.items()])
        
        resume.append({
            'Colonne': col,
            'Type': dtype,
            'Non-Nuls': non_null,
            'Nuls': null_count,
            '% Nuls': f"{null_pct:.1f}%",
            'Uniques': nunique,
            'Top 3 Valeurs': top_str
        })
    return pd.DataFrame(resume)

def comparer_structures(df_2023, df_2024, df_2025):
    """
    Compare les colonnes des trois DataFrames et retourne un tableau de synthèse.
    """
    cols23 = set(df_2023.columns)
    cols24 = set(df_2024.columns)
    cols25 = set(df_2025.columns)
    
    toutes_colonnes = sorted(list(cols23 | cols24 | cols25))
    
    comparaison = []
    for col in toutes_colonnes:
        comparaison.append({
            'Colonne': col,
            '2023': col in cols23,
            '2024': col in cols24,
            '2025': col in cols25
        })
    df = pd.DataFrame(comparaison)
    df['Toutes annees'] = df['2023'] & df['2024'] & df['2025']
    df['Presence'] = df['2023'].astype(int) + df['2024'].astype(int) + df['2025'].astype(int)
    return df

def notations_poules_par_individu_ou_groupe(df_2023, df_2024, df_2025, poules_2023, poules_2024, poules_2025):
    """
    Retourne les valeurs des notations des pontes par individu ou groupe.
    """
    notations = {}
    for df, poules in [(df_2023, poules_2023), (df_2024, poules_2024), (df_2025, poules_2025)]:
        for poule in poules:
            if poule in df.columns:
                notations_poule = df[poule].value_counts().to_dict()
                if poule in notations:
                    for notation, count in notations_poule.items():
                        notations[poule][notation] = notations[poule].get(notation, 0) + count
                else:
                    notations[poule] = notations_poule
    return notations

def get_other_columns_analysis(df, poules_list, year):
        # Colonnes à exclure (poules + Date)
    exclure = set(poules_list) | {'Date'}
    autres_cols = [c for c in df.columns if c not in exclure]
    
    results = []
    for col in autres_cols:
        unique_vals = df[col].dropna().unique()
        count = len(unique_vals)
        # Si c'est numérique et qu'il y a beaucoup de valeurs, on ne liste pas tout
        if df[col].dtype in ['float64', 'int64'] and count > 15:
            vals_str = f"{count} valeurs numériques (min: {df[col].min()}, max: {df[col].max()})"
        else:
            vals_str = ", ".join([str(v) for v in unique_vals[:20]])
            if count > 20:
                vals_str += "..."
        
        results.append({
            'Année': year,
            'Colonne': col,
            'Type': df[col].dtype,
            'Nombre Uniques': count,
            'Notations': vals_str
        })
    return pd.DataFrame(results)

def creer_tableau_notations_poules(notations_dict):
    """
    Crée un DataFrame avec les noms des poules en colonnes et les notations en lignes.
    """
    df_notations = pd.DataFrame(notations_dict)
    df_notations.index = df_notations.index.astype(str)
    df_notations = df_notations.sort_index()
    return df_notations

def audit_transverse():
    print("--- Démarrage de l'Audit Transverse des Données ---")

    # 1. Chargement des données
    print("\n[1/6] Chargement des fichiers Excel...")
    try:
        df_2023 = pd.read_excel('data/ponte_2023.xlsx')
        df_2024 = pd.read_excel('data/ponte_2024.xlsx')
        df_2025 = pd.read_excel('data/ponte_2025.xlsx')
        
        # Nettoyage des dates
        df_2023['Date'] = pd.to_datetime(df_2023['Date'], format='%d/%m/%Y', errors='coerce')
        df_2024['Date'] = pd.to_datetime(df_2024['Date'], format='%d/%m/%Y', errors='coerce')
        df_2025['Date'] = pd.to_datetime(df_2025['Date'], format='%d/%m/%Y', errors='coerce')
        
        print("✓ Fichiers chargés")
    except Exception as e:
        print(f"❌ Erreur lors du chargement : {e}")
        return

    # 2. Structure des colonnes
    print("\n[2/6] Analyse de la structure des colonnes...")
    df_comparaison = comparer_structures(df_2023, df_2024, df_2025)
    df_comparaison.to_csv('audit/audit_comparaison_colonnes.csv', index=False, encoding='utf-8-sig', sep=';')
    print("✓ audit_comparaison_colonnes.csv généré")

    # 3. Statistiques détaillées
    print("\n[3/6] Analyse statistique par année...")
    analyser_colonnes(df_2023).to_csv('audit/audit_stats_2023.csv', index=False, encoding='utf-8-sig', sep=';')
    analyser_colonnes(df_2024).to_csv('audit/audit_stats_2024.csv', index=False, encoding='utf-8-sig', sep=';')
    analyser_colonnes(df_2025).to_csv('audit/audit_stats_2025.csv', index=False, encoding='utf-8-sig', sep=';')
    print("✓ audit_stats_2023.csv, 2024.csv, 2025.csv générés")

    # 4. Inventaire des poules
    print("\n[4/6] Inventaire des poules et groupes...")
    poules_2023 = ['Joséphine', 'Albertine', 'Augustine', 'Cunégonde', 'Pioupioute', 'Valérie', 'Rémiel', 'Saquiel']
    poules_2024 = ['Joséphine', 'Albertine', 'Cunégonde', 'Valérie', 'Pioupioute', 'Rémiel', 'Nina et Tina', 'Marans', 'Nina', 'Tina']
    poules_2025 = ['Joséphine', 'Cunégonde', 'Valérie', 'Pioupioute', 'Rémiel', '3 Marans']

    toutes_poules = sorted(list(set(poules_2023) | set(poules_2024) | set(poules_2025)))
    presence_poules = []
    for p in toutes_poules:
        presence_poules.append({
            'Nom / Groupe': p,
            '2023': p in poules_2023,
            '2024': p in poules_2024,
            '2025': p in poules_2025
        })
    pd.DataFrame(presence_poules).to_csv('audit/audit_presence_poules_groupes.csv', index=False, encoding='utf-8-sig', sep=';')
    print("✓ audit_presence_poules_groupes.csv généré")

    # 5. Notations de pontes
    print("\n[5/6] Analyse des notations de pontes (matrice complète)...")
    notations_dict = notations_poules_par_individu_ou_groupe(df_2023, df_2024, df_2025, poules_2023, poules_2024, poules_2025)
    creer_tableau_notations_poules(notations_dict).to_csv('audit/audit_notations_poules.csv', encoding='utf-8-sig', sep=';')
    print("✓ audit_notations_poules.csv généré")


    # 6. Notations des données hors ponte
    print("\n[6/6] Analyse des autres notations (matrice complète)...")
    res_2023 = get_other_columns_analysis(df_2023, poules_2023, 2023)
    res_2024 = get_other_columns_analysis(df_2024, poules_2024, 2024)
    res_2025 = get_other_columns_analysis(df_2025, poules_2025, 2025)

    # Fusionner les résultats pour une vue d'ensemble
    all_results = pd.concat([res_2023, res_2024, res_2025], ignore_index=True)

    # Afficher le résultat final
    print("\nSynthèse des notations des colonnes techniques/météo :")
    print(all_results.to_string(index=False))

    # Sauvegarder pour consultation
    all_results.to_csv('audit/audit_notations_hors_poules.csv', index=False, encoding='utf-8-sig', sep=';')
    print("✓ audit_notations_hors_poules.csv généré")
    print("\n--- Audit terminé avec succès ! ---")

audit_transverse()
