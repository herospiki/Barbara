import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# Configuration de l'affichage
output_html = "output/step0_visualisation_audit.html"

def charger_donnees():
    """Charge les fichiers CSV du dossier audit."""
    fichiers = {
        'presence': 'data/audit/audit_presence_poules_groupes.csv',
        'comparaison': 'data/audit/audit_comparaison_colonnes.csv',
        'notations': 'data/audit/audit_notations_poules.csv',
        'stats_2023': 'data/audit/audit_stats_2023.csv',
        'stats_2024': 'data/audit/audit_stats_2024.csv',
        'stats_2025': 'data/audit/audit_stats_2025.csv'
    }
    
    dfs = {}
    for key, path in fichiers.items():
        if os.path.exists(path):
            dfs[key] = pd.read_csv(path, sep=';')
            # Nettoyage si besoin (ex: % Nuls en float)
            if 'stats' in key:
                dfs[key]['% Nuls Float'] = dfs[key]['% Nuls'].str.replace('%', '').astype(float)
    return dfs

def create_presence_heatmap(df):
    """Crée une heatmap de présence des poules."""
    df_plot = df.set_index('Nom / Groupe')
    # Transformer True/False en 1/0 pour la heatmap
    df_plot = df_plot.map(lambda x: 1 if x == True else 0)
    
    # La largeur de la heatmap doit être suffisante pour afficher correctement les étiquettes
    # et le contenu de la heatmap
    fig = px.imshow(df_plot, 
                    labels=dict(x="Année", y="Poule / Groupe", color="Présence"),
                    x=['2023', '2024', '2025'],
                    color_continuous_scale=[[0, 'rgba(239, 85, 59, 0.7)'], [1, 'rgba(0, 204, 150, 0.7)']],
                   # title="Présence des Poules et Groupes par Année", 
                    aspect="auto")
    
    fig.update_layout(
        coloraxis_showscale=False,
        xaxis_title="",
        yaxis_title="Nom de la poule / groupe"
    )
    # Ajouter du texte 'V' ou 'X' sur les cases
    for i, row in enumerate(df_plot.index):
        for j, col in enumerate(df_plot.columns):
            val = "✓" if df_plot.iloc[i, j] == 1 else "✗"
            fig.add_annotation(x=j, y=i, text=val, showarrow=False, font=dict(color="white", size=14))
            
    return fig

def create_missing_data_bar(dfs):
    """Crée un graphique comparatif des données manquantes."""
    data = []
    for year in ['2023', '2024', '2025']:
        key = f'stats_{year}'
        if key in dfs:
            df = dfs[key]
            # On prend les 15 colonnes avec le plus de nuls (hors Date)
            df_nuls = df[df['Colonne'] != 'Date'].sort_values('% Nuls Float', ascending=False).head(15)
            df_nuls['Année'] = year
            data.append(df_nuls)
    
    if not data:
        return go.Figure()
        
    df_combined = pd.concat(data)
    
    fig = px.bar(df_combined, 
                 x='Colonne', 
                 y='% Nuls Float', 
                 color='Année',
                 barmode='group',
                 title="Top 15 des colonnes avec le plus de données manquantes (%)",
                 labels={'% Nuls Float': 'Données manquantes (%)', 'Colonne': 'Nom de la colonne'},
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    
    fig.update_layout(xaxis_tickangle=-45)
    return fig

def create_notations_summary(df):
    """Crée un résumé des notations de pontes."""
    # Identifier et renommer la première colonne de notations
    first_col = df.columns[0]
    df_renamed = df.rename(columns={first_col: 'Notation'})
    
    # Nettoyage des données (remplacer les NaN par 0 pour le calcul)
    df_renamed = df_renamed.fillna(0)
    
    # Calcul de la fréquence totale (somme sur toutes les colonnes de poules)
    # On exclut la colonne 'Notation' du calcul de la somme
    colonnes_poules = [c for c in df_renamed.columns if c != 'Notation']
    df_renamed['Fréquence'] = df_renamed[colonnes_poules].sum(axis=1)
    
    # On ne garde que l'essentiel et on groupe par Notation
    df_plot = df_renamed.groupby('Notation')['Fréquence'].sum().reset_index()
    
    # Filtrer les notations qui ont une fréquence de 0
    df_plot = df_plot[df_plot['Fréquence'] > 0]
    
    # Trier par fréquence décroissante
    df_plot = df_plot.sort_values('Fréquence', ascending=False)
    
    # Création du graphique à barres
    fig = px.bar(df_plot,
                 x='Notation',
                 y='Fréquence',
                 title="Fréquence cumulée toutes poules",
                 labels={'Fréquence': 'Nombre total d\'occurrences', 'Notation': 'Type de notation'},
                 color='Fréquence',
                 color_continuous_scale='Viridis')
    
    # Forcer l'ordre décroissant et incliner les étiquettes
    fig.update_xaxes(categoryorder='total descending')
    fig.update_layout(xaxis_tickangle=-45)
    
    return fig

def create_column_comparison(df):
    """Crée un graphique de la présence des colonnes à travers les années."""
    df_plot = df.sort_values('Presence', ascending=True)
    
    fig = px.bar(df_plot, 
                 y='Colonne', 
                 x='Presence',
                 orientation='h',
                 title="Disponibilité des colonnes sur les 3 ans",
                 labels={'Presence': 'Nombre d\'années', 'Colonne': 'Nom de la colonne'},
                 color='Presence',
                 color_continuous_scale='Viridis')
    
    fig.update_layout(height=600, width=600)
    return fig

def generate_report():
    print("Chargement des données d'audit...")
    dfs = charger_donnees()
    
    if not dfs:
        print("Erreur : Aucun fichier d'audit trouvé dans le dossier 'audit/'.")
        return

    print("Génération des graphiques...")
    fig1 = create_presence_heatmap(dfs['presence'])
    fig2 = create_missing_data_bar(dfs)
    fig3 = create_notations_summary(dfs['notations'])
    fig4 = create_column_comparison(dfs['comparaison'])
    
    # Lecture des notations hors poules pour affichage tableau
    df_hors_poules = pd.read_csv('data/audit/audit_notations_hors_poules.csv', sep=';')
    table_html = df_hors_poules.to_html(classes='table table-striped', index=False)
    
    # Construction du HTML final avec un style premium
    html_content = f"""
    <html>
    <head>
        <title>Audit des Données - Barbara</title>
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
                transition: transform 0.2s ease;
            }}
            h1 {{ font-weight: 800; letter-spacing: -1px; }}
            h2 {{ color: #1e3c72; font-weight: 700; margin-bottom: 20px; border-left: 5px solid #1e3c72; padding-left: 15px; }}
            .table-container {{ overflow-x: auto; }}
            .stat-card {{
                background: #fff;
                padding: 20px;
                border-radius: 12px;
                text-align: center;
                border-bottom: 4px solid #1e3c72;
            }}
            .stat-value {{ font-size: 2rem; font-weight: 800; color: #1e3c72; }}
            .stat-label {{ color: #6c757d; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 1px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 Audit Transverse des Données</h1>
            <p class="lead">Projet de suivi de ponte "Barbara" - Analyse 2023 à 2025</p>
        </div>
        
        <div class="container pb-5">
            <!-- KPIs -->
            <div class="row mb-5">
            <div class="col-md-4">
                    <div class="stat-card">
                        <div class="stat-value">3</div>
                        <div class="stat-label">Années</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card">
                        <div class="stat-value">{len(dfs['presence'])}</div>
                        <div class="stat-label">Sujets mentionnés</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card">
                        <div class="stat-value">{len(dfs['comparaison'])}</div>
                        <div class="stat-label">Colonnes analysées</div>
                    </div>
                </div>
                
            </div>

            <div class="row">
                <div class="col-lg-6">
                    <div class="card">
                        <h2>🧬 Présence des Sujets par Année</h2>
                        {fig1.to_html(full_html=False, include_plotlyjs='cdn')}
                    </div>
                    <div class="card" style="min-height: 100px;">
                        📝 Analyse de la Cohorte
                        <p><i>Insérez vos observations ici :</i></p>
                    </div>
                </div>
                <div class="col-lg-6">
                    <div class="card">
                        <h2>📋 Structure des Fichiers</h2>
                        {fig4.to_html(full_html=False, include_plotlyjs=False)}
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>📉 Qualité & Complétude</h2>
                <p class="text-muted">Top 15 des colonnes par taux de données manquantes (Nuls).</p>
                {fig2.to_html(full_html=False, include_plotlyjs=False)}
            </div>

            <div class="card">
                <h2>🥚 Répartition des Notations (Pontes)</h2>
                {fig3.to_html(full_html=False, include_plotlyjs=False)}
            </div>
            
            <div class="card">
                <h2>🛠️ Détails Techniques & Météo</h2>
                <div class="table-container">
                    {table_html}
                </div>
            </div>
        </div>

        <footer class="text-center py-4 text-muted">
            Généré automatiquement par Antigravity - {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}
        </footer>
    </body>
    </html>
    """
    
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"✓ Rapport complet généré : {output_html}")
    print("Ouvrez ce fichier dans votre navigateur pour visualiser les graphiques.")

if __name__ == "__main__":
    generate_report()