import pandas as pd
import datetime as dt
import plotly.express as px
import plotly.graph_objects as go
import os

def generate_step5_visualization():
    # 1. Charger les données
    try:
        df = pd.read_csv('interim/tableau_commentaires.csv', sep=';')
    except FileNotFoundError:
        print("Erreur : Fichier interim/tableau_commentaires.csv non trouvé.")
        return

    # 2. Préparation des statistiques
    total_comments = len(df[df['Commentaires_clean'].notna() & (df['Commentaires_clean'] != "")])
    non_autre = len(df[df['Catégorie'] != 'Autre'])
    
    # Statistiques par catégorie
    cat_counts = df[df['Commentaires_clean'].notna()]['Catégorie'].value_counts().reset_index()
    cat_counts.columns = ['Catégorie', 'Nombre']
    
    # Top poules citées
    all_poules = df['Poules_Citées'].str.split(', ').explode()
    poule_counts = all_poules[all_poules != 'Aucune'].value_counts()
    top_poule = poule_counts.index[0] if not poule_counts.empty else "N/A"
    
    # 3. Création du graphique Plotly (Distribution des catégories)
    fig = px.bar(cat_counts, x='Nombre', y='Catégorie', orientation='h', 
                 title="Distribution des Catégories de Commentaires",
                 color='Nombre', color_continuous_scale='Blues')
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                      margin=dict(l=20, r=20, t=40, b=20), height=400)
    
    graph_html = fig.to_html(full_html=False, include_plotlyjs='cdn')

    # 4. Génération du HTML
    html_content = f"""
    <html>
    <head>
        <title>Analyse Commentaires - Barbara</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f4f7f6;
                margin: 0;
                padding: 0;
            }}
            .header {{
                background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
                color: white;
                padding: 50px 20px;
                text-align: center;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                margin-bottom: 30px;
            }}
            .container {{ max-width: 1300px; }}
            .card {{
                background: white;
                border: none;
                border-radius: 15px;
                box-shadow: 0 5px 20px rgba(0,0,0,0.05);
                margin-bottom: 30px;
                padding: 25px;
            }}
            h1 {{ font-weight: 800; letter-spacing: -1px; }}
            h2 {{ color: #27ae60; font-weight: 700; margin-bottom: 20px; border-left: 5px solid #27ae60; padding-left: 15px; }}
            .stat-card {{
                background: #fff;
                padding: 20px;
                border-radius: 12px;
                text-align: center;
                border-bottom: 4px solid #27ae60;
                margin-bottom: 20px;
            }}
            .stat-value {{ font-size: 2.2rem; font-weight: 800; color: #27ae60; }}
            .stat-label {{ color: #7f8c8d; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 1px; font-weight: 600; }}
            .table-container {{ overflow-x: auto; }}
            thead th {{ 
                background-color: #f1f4f9 !important; 
                text-align: left !important; 
                color: #2c3e50;
                font-weight: 700;
            }}
            .cat-badge {{
                padding: 4px 8px;
                border-radius: 8px;
                font-size: 0.75rem;
                font-weight: 600;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>💬 Analyse des Commentaires & Journal (Step 5)</h1>
            <p class="lead">Extraction de connaissances textuelles et suivi de santé des poules</p>
        </div>
        
        <div class="container pb-5">
            <!-- KPIs -->
            <div class="row mb-4">
                <div class="col-md-4">
                    <div class="stat-card">
                        <div class="stat-value">{total_comments}</div>
                        <div class="stat-label">Total Segments de texte</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card">
                        <div class="stat-value">{non_autre}</div>
                        <div class="stat-label">Commentaires Thématiques classés</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card">
                        <div class="stat-value">{top_poule}</div>
                        <div class="stat-label">Poule la plus citée</div>
                    </div>
                </div>
            </div>

            <div class="row">
                <div class="col-lg-7">
                    <div class="card">
                        <h2>📊 Distribution Thématique</h2>
                        {graph_html}
                    </div>
                </div>
                <div class="col-lg-5">
                    <div class="card">
                        <h2>🐔 Citations par Poule</h2>
                        <div class="table-container">
                            {poule_counts.head(10).to_frame().reset_index().to_html(classes='table table-sm table-hover', index=False, header=('Nom', 'Citations'))}
                        </div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>🔍 Zoom sur les Catégories Prioritaires</h2>
                <p class="text-muted">Extrait de commentaires significatifs par catégorie :</p>
                <div class="table-container">
                    <table class="table table-sm table-hover bg-white">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Commentaire Nettoyé</th>
                                <th>Catégorie</th>
                                <th>Poules Citées</th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join([f"<tr><td>{row['Date']}</td><td>{row['Commentaires_clean']}</td><td><span class='cat-badge bg-light text-dark'>{row['Catégorie']}</span></td><td>{row['Poules_Citées']}</td></tr>" 
                                      for _, row in df[df['Catégorie'] != 'Autre'].head(15).iterrows()])}
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="card">
                <h2>📝 Méthodologie d'Analyse</h2>
                <ul class="list-group list-group-flush">
                    <li class="list-group-item"><b>Explosion des données :</b> Séparation des notations multiples pour traiter chaque observation individuellement.</li>
                    <li class="list-group-item"><b>Reconnaissance d'Entités :</b> Détection automatique des noms de poules dans le texte libre.</li>
                    <li class="list-group-item"><b>Priorisation :</b> Si un commentaire mentionne à la fois la santé et la météo, la priorité est donnée aux aspects de santé pour l'alerte.</li>
                    <li class="list-group-item"><b>Journal de Bord :</b> Transformation de notes informelles en base de données structurée pour corrélation future avec la ponte.</li>
                </ul>
            </div>
        </div>
        
        <footer class="text-center py-4 text-muted border-top">
            Généré automatiquement par Antigravity - Analyse Commentaires Step 5 - {dt.datetime.now().strftime('%d/%m/%Y %H:%M')}
        </footer>
    </body>
    </html>
    """
    
    with open('interim/step5_visualisation_analyse_commentaires.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("Visualisation générée : interim/step5_visualisation_analyse_commentaires.html")

if __name__ == "__main__":
    generate_step5_visualization()
