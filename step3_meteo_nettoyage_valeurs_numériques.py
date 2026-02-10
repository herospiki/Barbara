import pandas as pd
import datetime as dt

def charger_donnees():
    df_meteo = pd.read_csv('interim/df_1_meteo.csv', sep=';')
    return df_meteo

print(charger_donnees())

def audit_meteo(df_meteo):
    print(df_meteo.head())
    print(df_meteo.info())
    print(df_meteo.describe())
    print(df_meteo.isnull().sum())

audit_meteo(charger_donnees())

# On remarque que la colonne 'Météo' a des valeurs manquantes et des valeurs multiples (ex: 'beau/couvert').
# Les valeurs manquantes seront remplacées par 'inconnue'
# Les valeurs multiples feront l'objet d'un traitement spécifique
# On remarque que la colonne 'Pluie(mm)' a des valeurs manquantes : elles seront remplacées
# par zéro
# On remarque que la colonne 'T°C (12h-15h)' a des valeurs manquantes : ici on remplacera
# les valeurs manquantes par la moyenne des valeurs de la date précédente avec valeurs valides et la date suivante 
# avec valeurs valides  
# On remarque que la colonne 'Humidité' a des valeurs manquantes : ici on remplacera
# les valeurs manquantes par la moyenne des valeurs de la date précédente avec valeurs valides et la date suivante 
# avec valeurs valides pour les années 2024 et 2025 car en 2023 il n'y a pas de donnée

def traitement_pluie(df_meteo):
    df_meteo['Pluie(mm)'] = df_meteo['Pluie(mm)'].fillna(0)
    return df_meteo

def traitement_temperature(df_meteo):
    # On crée une fonction pour remplacer les valeurs manquantes par la moyenne des valeurs de la date précédente avec valeurs valides et la date suivante 
    # avec valeurs valides. 
    # On crée une nouvelle colonne pour stocker les valeurs traitées : 'T°C (12h-15h)_traite'
    df_meteo['T°C (12h-15h)_traite'] = df_meteo['T°C (12h-15h)']
    for i in range(len(df_meteo)):
        if pd.isna(df_meteo.loc[i, 'T°C (12h-15h)']):
            df_meteo.loc[i, 'T°C (12h-15h)_traite'] = float(df_meteo.loc[i-1, 'T°C (12h-15h)'] + df_meteo.loc[i+1, 'T°C (12h-15h)'])/2
    return df_meteo

def traitement_humidite(df_meteo):
    # On crée une fonction pour remplacer les valeurs manquantes par la moyenne des valeurs de la date précédente avec valeurs valides et la date suivante 
    # avec valeurs valides  
    # On crée une nouvelle colonne pour stocker les valeurs traitées : 'Humidité_traite'
    # Attention, il faut tester l'année !
    df_meteo['Humidité_traite'] = df_meteo['Humidité']
    df_meteo['Date'] = pd.to_datetime(df_meteo['Date'])
    if df_meteo['Date'].dt.year.isin([2024, 2025]).any():
        # On récupère les valeurs manquantes hors 2023
        mask = df_meteo['Humidité'].isna()
        # On calcule la moyenne des valeurs de la date précédente avec valeurs valides et la date suivante 
        # avec valeurs valides
        avg_values = (df_meteo['Humidité'].shift(1) + df_meteo['Humidité'].shift(-1)) / 2
        # On remplace les valeurs manquantes par la moyenne des valeurs de la date précédente avec valeurs valides et la date suivante 
        # avec valeurs valides
        df_meteo.loc[mask, 'Humidité_traite'] = avg_values[mask]
    return df_meteo


def traitement_meteo(df_meteo):
    df_meteo['Date'] = pd.to_datetime(df_meteo['Date'])
    df_meteo = traitement_pluie(df_meteo)
    df_meteo = traitement_temperature(df_meteo)
    df_meteo = traitement_humidite(df_meteo)
    return df_meteo

df_meteo_clean = traitement_meteo(charger_donnees())

df_meteo_clean.to_csv('interim/df_2_meteo_clean.csv', sep=';', index=False)



