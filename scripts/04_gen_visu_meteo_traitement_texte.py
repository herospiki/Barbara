import pandas as pd
import datetime as dt
import os

def generate_step4_visualization():
    # 1. Charger les données
    # On compare idéalement df_2 (numérique nettoyé) et df_3 (texte traité et catégorisé)
    try:
        df2 = pd.read_csv('data/intermediaire/df_2_meteo.csv', sep=';')
        df3 = pd.read_csv('data/intermediaire/df_3_meteo.csv', sep=';')
    except FileNotFoundError:
        print("Erreur : Fichiers intermediaire non trouvés. Assurez-vous d'avoir exécuté 04_meteo_traitement_texte.py")
        return

    # 2. Préparation des statistiques
    total_obs = len(df3)
    # Nombre de lignes avec des météos multiples (présence d'un '/')
    meteos_multiples = df3['Météo'].str.contains('/', na=False).sum()
    
    # Statistiques sur les catégories pour toutes les valeurs des colonnes Météo_1_Cat, Météo_2_Cat, Météo_3_Cat, Météo_4_Cat
    cat_counts = pd.concat([
        df3['Météo_1_Cat'], 
        df3['Météo_2_Cat'], 
        df3['Météo_3_Cat'], 
        df3['Météo_4_Cat']
    ]).value_counts()
    top_cat = cat_counts.index[0] if not cat_counts.empty else "N/A"
    top_cat_val = cat_counts.iloc[0] if not cat_counts.empty else 0

    cat_journalieres_counts = df3['Météo_Cat'].value_counts()
    
    """ if 'Météo_1_Cat' in df3.columns:
        cat_counts = df3['Météo_1_Cat'].value_counts()
        top_cat = cat_counts.index[0] if not cat_counts.empty else "N/A"
        top_cat_val = cat_counts.iloc[0] if not cat_counts.empty else 0
    else:
        top_cat = "N/A"
        top_cat_val = 0 """

    # 3. Exemples de transformations

    # On cherche des lignes où Météo != Météo_Corrigée (corrections orthographiques)
   # corrections = df3[df3['Météo'].str.lower() != df3['Météo_Corrigée'].str.lower()].head(3)
    
    # On cherche des lignes avec split (Météo_2 non nul)
   # splits = df3[df3['Météo_2'].notna()].head(3)

    # Récupération dynamique des détails des catégories
    mappings = []
    for i in range(1, 5): # Météo_1 à Météo_4
        col_term = f'Météo_{i}'
        col_cat = f'Météo_{i}_Cat'
        if col_term in df3.columns and col_cat in df3.columns:
            subset = df3[[col_term, col_cat]].dropna().drop_duplicates()
            mappings.append(subset.rename(columns={col_term: 'Terme', col_cat: 'Categorie'}))
    
    details_html = ""
    if mappings:
        all_mappings = pd.concat(mappings).drop_duplicates().sort_values('Terme')
        cat_details = all_mappings.groupby('Categorie')['Terme'].apply(list).to_dict()
        
        for cat, terms in sorted(cat_details.items()):
            terms_str = ", ".join(sorted(terms))
            details_html += f"""
            <li class="list-group-item">
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1 text-primary">{cat}</h6>
                    <small class="badge bg-light text-dark">{len(terms)} variantes</small>
                </div>
                <p class="mb-1 small text-muted" style="line-height: 1.4;">{terms_str}</p>
            </li>
            """
    else:
        details_html = "<li class='list-group-item'>Aucune donnée de catégorie trouvée.</li>"

    # 4. Génération du HTML
    html_content = f"""
    <html>
    <head>
        <title>Traitement Texte Météo - Barbara</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f8f9fa;
                margin: 0;
                padding: 0;
            }}
            .header {{
                background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
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
                box-shadow: 0 10px 30px rgba(0,0,0,0.05);
                margin-bottom: 40px;
                padding: 25px;
            }}
            h1 {{ font-weight: 800; letter-spacing: -1px; }}
            h2 {{ color: #2c3e50; font-weight: 700; margin-bottom: 20px; border-left: 5px solid #3498db; padding-left: 15px; }}
            .stat-card {{
                background: #fff;
                padding: 20px;
                border-radius: 12px;
                text-align: center;
                border-bottom: 4px solid #3498db;
                margin-bottom: 20px;
                transition: transform 0.3s;
            }}
            .stat-card:hover {{ transform: translateY(-5px); }}
            .stat-value {{ font-size: 2.2rem; font-weight: 800; color: #2c3e50; }}
            .stat-label {{ color: #7f8c8d; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 1px; font-weight: 600; }}
            .table-container {{ overflow-x: auto; }}
            thead th {{ 
                background-color: #f1f4f9 !important; 
                text-align: left !important; 
                color: #2c3e50;
                font-weight: 700;
                border-bottom: 2px solid #dee2e6 !important;
            }}
            .badge-cat {{
                background-color: #3498db;
                color: white;
                padding: 5px 10px;
                border-radius: 12px;
                font-size: 0.8rem;
            }}
            .arrow {{ color: #95a5a6; margin: 0 10px; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📝 Traitement Textuel & Catégorisation (Step 4)</h1>
            <p class="lead">Normalisation des libellés météo, split des conditions multiples et mapping thématique</p>
        </div>
        
        <div class="container pb-5">
            <!-- KPIs -->
            <div class="row mb-4">
                <div class="col-md-4">
                    <div class="stat-card">
                        <div class="stat-value">{meteos_multiples}</div>
                        <div class="stat-label">Obs. avec multi-conditions (split)</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card">
                        <div class="stat-value">{top_cat}</div>
                        <div class="stat-label">Catégorie la plus fréquente</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card">
                        <div class="stat-value">{total_obs}</div>
                        <div class="stat-label">Total Observations classées</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>🛠️ Logique de Nettoyage et Correction</h2>
                <div class="table-container">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>Type d'Action</th>
                                <th>Entrée Brute</th>
                                <th>Transformation</th>
                                <th>Résultat</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><b>Correction Orthographique</b></td>
                                <td class="text-muted">acalmie, éclairicie</td>
                                <td class="arrow">→</td>
                                <td><span class="badge bg-success">accalmie, éclaircies</span></td>
                            </tr>
                            <tr>
                                <td><b>Normalisation Séparateur</b></td>
                                <td class="text-muted">beau puis bruine</td>
                                <td class="arrow">→</td>
                                <td><span class="badge bg-info">beau/bruine</span></td>
                            </tr>
                            <tr>
                                <td><b>Split de Colonnes</b></td>
                                <td class="text-muted">"Soleil/Vent"</td>
                                <td class="arrow">→</td>
                                <td>Col 1: <code>Soleil</code> | Col 2: <code>Vent</code></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="card">
                <h2>🏷️ Mapping en Catégories</h2>
                <div class="row">
                    <div class="col-md-6">
                        <p>Détail des termes pour chaque catégorie :</p>
                        <ul class="list-group list-group-flush" style="max-height: 500px; overflow-y: auto;">
                            {details_html}
                        </ul>
                    </div>
                    <div class="col-md-6 border-start">
                        <p class="text-center font-weight-bold"><b>Répartition Top 5 Catégories</b></p>
                        <div class="table-container">
                            {cat_counts.head(5).to_frame().reset_index().to_html(classes='table table-sm table-borderless', index=False, header=False)}
                        </div>
                        <p class="text-center font-weight-bold"><b>Répartition Top 10 - Mentions journalières</b></p>
                        <div class="table-container">
                            {cat_journalieres_counts.head(10).to_frame().reset_index().to_html(classes='table table-sm table-borderless', index=False, header=False)}
                        </div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>📊 Aperçu des Données Catégorisées (df_3)</h2>
                <p class="text-muted">Colonnes splittées et leurs catégories associées :</p>
                <div class="table-container">
                    {df3[['Date', 'Météo','Météo_Clean', 'Météo_1_Cat',  'Météo_2_Cat','Météo_3_Cat','Météo_4_Cat','Météo_Cat']].head(12).to_html(classes='table table-sm table-hover bg-white', index=False, justify='left')}
                </div>
            </div>

            <div class="card">
                <h2>📝 Synthèse du Traitement</h2>
                <ul class="list-group list-group-flush">
                    <li class="list-group-item"><b>Mapping Correctif :</b> 18 expressions courantes corrigées avant traitement.</li>
                    <li class="list-group-item"><b>Multi-Conditions :</b> Jusqu'à 4 conditions simultanées capturées par observation.</li>
                    <li class="list-group-item"><b>Robustesse :</b> Gestion des majuscules/minuscules et des espaces superflus.</li>
                    <li class="list-group-item"><b>Finalité :</b> Transition d'un texte libre vers des variables catégorielles exploitables en Machine Learning ou Statistique.</li>
                </ul>
            </div>
        </div>
        
        <footer class="text-center py-4 text-muted border-top">
            Généré automatiquement par Antigravity - Traitement Texte Step 4 - {dt.datetime.now().strftime('%d/%m/%Y %H:%M')}
        </footer>
    </body>
    </html>
    """
    
    with open('output/step4_visualisation_meteo_traitement_texte.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("Visualisation générée : output/step4_visualisation_meteo_traitement_texte.html")

if __name__ == "__main__":
    generate_step4_visualization()
