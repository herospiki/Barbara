import pandas as pd
import numpy as np
from fonctions_utilitaires import analyser_colonnes

# Charger les données
df_2023 = pd.read_excel('ponte_2023.xlsx')
df_2024 = pd.read_excel('ponte_2024.xlsx')
df_2025 = pd.read_excel('ponte_2025.xlsx')

# Définir les listes de poules (basé sur l'audit transverse)
poules_2023 = ['Joséphine', 'Albertine', 'Augustine', 'Cunégonde', 'Pioupioute', 'Valérie', 'Rémiel', 'Saquiel']
poules_2024 = ['Joséphine', 'Albertine', 'Cunégonde', 'Valérie', 'Pioupioute', 'Rémiel', 'Nina et Tina', 'Marans', 'Nina', 'Tina']
poules_2025 = ['Cunégonde', 'Valérie', '3 Marans', 'Joséphine', 'Rémiel', 'Pioupioute']

all_poules_cols = set(poules_2023 + poules_2024 + poules_2025)

def get_other_columns_analysis(df, poules_list, year):
    # Colonnes à exclure (poules + Date)
    exclure = set(poules_list) | {'Date'}
    autres_cols = [c for c in df.columns if c not in exclure]
    
    print(f"\n--- Analyse des colonnes hors poules pour {year} ---")
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

res_2023 = get_other_columns_analysis(df_2023, poules_2023, 2023)
res_2024 = get_other_columns_analysis(df_2024, poules_2024, 2024)
res_2025 = get_other_columns_analysis(df_2025, poules_2025, 2025)

# Fusionner les résultats pour une vue d'ensemble
all_results = pd.concat([res_2023, res_2024, res_2025], ignore_index=True)

# Afficher le résultat final
print("\nSynthèse des notations des colonnes techniques/météo :")
print(all_results.to_string(index=False))

# Sauvegarder pour consultation
all_results.to_csv('analyse_notations_hors_poules.csv', index=False, encoding='utf-8-sig', sep=';')
print("\nL'analyse a été sauvegardée dans 'analyse_notations_hors_poules.csv'")
