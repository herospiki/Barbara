import pandas as pd
import datetime as dt
import plotly.graph_objects as go
import os

def generate_visualization():
    # 1. Charger les données
    df1 = pd.read_csv('data/intermediaire/df_1_meteo.csv', sep=';')
    df2 = pd.read_csv('data/intermediaire/df_2_meteo.csv', sep=';')
    
    # S'assurer que les dates sont au bon format pour la comparaison
    df1['Date'] = pd.to_datetime(df1['Date'])
    df2['Date'] = pd.to_datetime(df2['Date'])
    
    # 2. Calculer les statistiques
    total_rows = len(df1)
    pluie_nans = df1['Pluie(mm)'].isna().sum()
    temp_nans = df1['T°C (12h-15h)'].isna().sum()
    hum_nans = df1['Humidité'].isna().sum()
    
    # 3. Identifier des exemples de lignes modifiées
    # Pluie (Remplacement par 0)
    ex_pluie = df1[df1['Pluie(mm)'].isna()].head(3).copy()
    if not ex_pluie.empty:
        ex_pluie['Action'] = 'Remplacement par 0'
    
    # Température (Interpolation)
    modified_temp = df1[df1['T°C (12h-15h)'].isna()].index
    ex_temp = df2.loc[modified_temp].head(3).copy()
    if not ex_temp.empty:
        ex_temp['Action'] = 'Interpolation (Moyenne J-1/J+1)'
        
    # 4. Générer le HTML (Style inspiré de Step 2)
    html_content = f"""
    <html>
    <head>
        <title>Nettoyage Météo - Barbara</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f1f4f9;
                margin: 0;
                padding: 0;
            }}
            .header {{
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: white;
                padding: 50px 20px;
                text-align: center;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                margin-bottom: 30px;
            }}
            .container {{ max-width: 1300px; }}
            .card {{
                background: white;
                border: none;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.08);
                margin-bottom: 40px;
                padding: 25px;
            }}
            h1 {{ font-weight: 800; letter-spacing: -1px; }}
            h2 {{ color: #1e3c72; font-weight: 700; margin-bottom: 20px; border-left: 5px solid #1e3c72; padding-left: 15px; }}
            .stat-card {{
                background: #fff;
                padding: 20px;
                border-radius: 12px;
                text-align: center;
                border-bottom: 4px solid #1e3c72;
                margin-bottom: 20px;
            }}
            .stat-value {{ font-size: 2rem; font-weight: 800; color: #1e3c72; }}
            .stat-label {{ color: #6c757d; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 1px; }}
            .table-container {{ overflow-x: auto; }}
            .comparison-table th {{ background-color: #f8f9fa; }}
            .highlight-cell {{ background-color: #e3f2fd; font-weight: bold; color: #0d47a1; }}
            thead th {{ 
                background-color: #f8f9fa !important; 
                text-align: left !important; 
                vertical-align: middle;
                border-bottom: 2px solid #dee2e6 !important;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🌦️ Nettoyage des Données Météo (Step 3)</h1>
            <p class="lead">Traitement des valeurs manquantes et normalisation numérique</p>
        </div>
        
        <div class="container pb-5">
            <!-- KPIs -->
            <div class="row mb-4">
                <div class="col-md-4">
                    <div class="stat-card">
                        <div class="stat-value">{pluie_nans}</div>
                        <div class="stat-label">Valeurs de Pluie complétées (0)</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card">
                        <div class="stat-value">{temp_nans}</div>
                        <div class="stat-label">Températures interpolées</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card">
                        <div class="stat-value">{hum_nans}</div>
                        <div class="stat-label">Valeurs d'Humidité traitées (2024-25)</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>🔍 Exemples de Nettoyage (Pluie & Température)</h2>
                <div class="table-container">
                    <table class="table table-bordered table-striped table-hover bg-white">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Ancienne Valeur</th>
                                <th>Valeur Nettoyée</th>
                                <th>Variable</th>
                                <th>Action effectuée</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>Exemple Pluie</td>
                                <td class="text-danger">NaN</td>
                                <td class="highlight-cell">0.0</td>
                                <td>Pluie(mm)</td>
                                <td>Remplacement systématique</td>
                            </tr>
                            <tr>
                                <td>Exemple T°C</td>
                                <td class="text-danger">NaN</td>
                                <td class="highlight-cell">Moyenne (prev, next)</td>
                                <td>T°C (12h-15h)_traite</td>
                                <td>Interpolation linéaire simple</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="card">
                <h2>📊 Aperçu des Données (T°C vs Humidité)</h2>
                <p class="text-muted">Aperçu des 10 premières lignes du fichier final :</p>
                <div class="table-container">
                    {df2.head(10).to_html(classes='table table-sm table-hover bg-white', index=False, justify='left')}
                </div>
            </div>

            <div class="card">
                <h2>📝 Synthèse du Nettoyage Météo</h2>
                <ul class="list-group list-group-flush">
                    <li class="list-group-item"><b>Traitement de la Pluie :</b> Les valeurs NaN sont considérées comme une absence de pluie (0.0 mm).</li>
                    <li class="list-group-item"><b>Interpolation de la Température :</b> Utilisation de la moyenne entre le jour précédent et le jour suivant pour boucher les trous isolés.</li>
                    <li class="list-group-item"><b>Gestion de l'Humidité :</b> Traitement similaire à la température, mais uniquement pour les années 2024 et 2025 (absence de capteur en 2023).</li>
                    <li class="list-group-item"><b>Uniformisation :</b> Création de nouvelles colonnes "traite" pour garder la trace des données brutes originales.</li>
                </ul>
            </div>
        </div>
        
        <footer class="text-center py-4 text-muted border-top">
            Généré automatiquement par Antigravity - Visualisation Météo Step 3 - {dt.datetime.now().strftime('%d/%m/%Y %H:%M')}
        </footer>
    </body>
    </html>
    """
    
    with open('output/step3_visualisation_nettoyage_meteo.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("Visualisation générée : output/step3_visualisation_nettoyage_meteo.html")

if __name__ == "__main__":
    generate_visualization()