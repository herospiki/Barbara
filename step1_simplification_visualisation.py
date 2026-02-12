import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# Configuration
output_html = "interim/step1_simplification_visualisation.html"

def load_data():
    """Charge les fichiers générés par le nouveau step1."""
    files = {
        'pontes': 'interim/df_1_pontes.csv',
        'marans_individuels': 'interim/df_1_marans_individuels.csv'
    }
    dfs = {}
    for key, path in files.items():
        if os.path.exists(path):
            df = pd.read_csv(path, sep=';')
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
            dfs[key] = df
    return dfs

def create_before_after_sankey():
    """Visualise la simplification du traitement Marans : Avant vs Après."""
    # AVANT : Logique complexe avec 3 niveaux
    links_before = [
        # Sources
        ("Albertine (2023)", "MARANS_TOTAL", "Renommage"),
        ("Nina (2024)", "NINA_TINA", "Sous-groupe"),
        ("Tina (2024)", "NINA_TINA", "Sous-groupe"),
        ("Marans (groupe)", "MARANS_TOTAL", "Direct"),
        ("Nina et Tina", "NINA_TINA", "Direct"),
        
        # Traitement
        ("MARANS_TOTAL", "niveau_observation=groupe", ""),
        ("NINA_TINA", "niveau_observation=sous-groupe", ""),
        ("Albertine (2023)", "niveau_observation=individuel", ""),
        ("Nina (2024)", "niveau_observation=individuel", ""),
        ("Tina (2024)", "niveau_observation=individuel", ""),
        
        # Sortie
        ("niveau_observation=groupe", "df_1_pontes (8770 lignes)", "Avec doublons"),
        ("niveau_observation=sous-groupe", "df_1_pontes (8770 lignes)", "Avec doublons"),
        ("niveau_observation=individuel", "df_1_pontes (8770 lignes)", "Avec doublons"),
    ]
    
    all_nodes_before = list(dict.fromkeys([l[0] for l in links_before] + [l[1] for l in links_before]))
    node_map_before = {name: i for i, name in enumerate(all_nodes_before)}
    
    def get_node_color_before(name):
        if "df_1" in name: return "#e74c3c"  # Rouge (Problème: doublons)
        if "niveau" in name: return "#f39c12"  # Orange
        if "TOTAL" in name or "NINA_TINA" in name: return "#e67e22"  # Orange foncé
        return "#95a5a6"  # Gris (Sources)
    
    fig_before = go.Figure(data=[go.Sankey(
        node = dict(
          pad = 15, thickness = 20,
          line = dict(color = "black", width = 0.5),
          label = all_nodes_before,
          color = [get_node_color_before(n) for n in all_nodes_before]
        ),
        link = dict(
          source = [node_map_before[l[0]] for l in links_before],
          target = [node_map_before[l[1]] for l in links_before],
          value = [1] * len(links_before),
          customdata = [l[2] for l in links_before],
          hovertemplate = '%{source.label} → %{target.label}<br />%{customdata}<extra></extra>'
        ))])
    
    fig_before.update_layout(
        title_text="❌ AVANT : Logique Complexe avec Doublons",
        font_size=11,
        height=500,
        margin=dict(t=60)
    )
    
    # APRÈS : Logique simplifiée
    links_after = [
        # Sources
        ("Albertine", "Fusion par Date", "Regroupement"),
        ("Nina", "Fusion par Date", "Regroupement"),
        ("Tina", "Fusion par Date", "Regroupement"),
        ("Nina et Tina", "Fusion par Date", "Regroupement"),
        ("Marans (groupe)", "Fusion par Date", "Regroupement"),
        
        # Sauvegarde individuelle
        ("Albertine", "df_1_marans_individuels.csv", "Conservation"),
        ("Nina", "df_1_marans_individuels.csv", "Conservation"),
        ("Tina", "df_1_marans_individuels.csv", "Conservation"),
        ("Nina et Tina", "df_1_marans_individuels.csv", "Conservation"),
        
        # Traitement
        ("Fusion par Date", "MARANS (unifié)", "1 ligne/date"),
        
        # Sortie
        ("MARANS (unifié)", "df_1_pontes (7306 lignes)", "Sans doublons"),
    ]
    
    all_nodes_after = list(dict.fromkeys([l[0] for l in links_after] + [l[1] for l in links_after]))
    node_map_after = {name: i for i, name in enumerate(all_nodes_after)}
    
    def get_node_color_after(name):
        if "df_1_pontes" in name: return "#2ecc71"  # Vert (Solution: propre)
        if "df_1_marans_individuels" in name: return "#3498db"  # Bleu (Archive)
        if "Fusion" in name or "MARANS (unifié)" in name: return "#f39c12"  # Orange
        return "#95a5a6"  # Gris (Sources)
    
    fig_after = go.Figure(data=[go.Sankey(
        node = dict(
          pad = 15, thickness = 20,
          line = dict(color = "black", width = 0.5),
          label = all_nodes_after,
          color = [get_node_color_after(n) for n in all_nodes_after]
        ),
        link = dict(
          source = [node_map_after[l[0]] for l in links_after],
          target = [node_map_after[l[1]] for l in links_after],
          value = [1] * len(links_after),
          customdata = [l[2] for l in links_after],
          hovertemplate = '%{source.label} → %{target.label}<br />%{customdata}<extra></extra>'
        ))])
    
    fig_after.update_layout(
        title_text="✅ APRÈS : Logique Simplifiée sans Doublons",
        font_size=11,
        height=500,
        margin=dict(t=60)
    )
    
    return fig_before, fig_after

def create_data_reduction_viz(dfs):
    """Visualise la réduction du volume de données."""
    # Données avant/après
    categories = ['Lignes totales', 'Lignes MARANS', 'Fichiers intermédiaires']
    avant = [8770, 2560, 3]  # 8770 lignes, 2560 MARANS (doublons), 3 fichiers (df_1_pontes, df_2_marans, df_2_hors_marans)
    apres = [7306, 1096, 2]  # 7306 lignes, 1096 MARANS (fusionné), 2 fichiers (df_1_pontes, df_1_marans_individuels)
    
    fig = go.Figure(data=[
        go.Bar(name='Avant', x=categories, y=avant, marker_color='#e74c3c', text=avant, textposition='auto'),
        go.Bar(name='Après', x=categories, y=apres, marker_color='#2ecc71', text=apres, textposition='auto')
    ])
    
    fig.update_layout(
        title="Réduction du Volume de Données et de la Complexité",
        barmode='group',
        yaxis_title="Nombre",
        template="plotly_white",
        height=400,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig

def create_effectif_by_year_viz(dfs):
    """Visualise l'effectif MARANS par année."""
    if 'pontes' not in dfs or dfs['pontes'] is None:
        return None
    
    df = dfs['pontes']
    marans = df[df['Poule_brute'] == 'MARANS'].copy()
    
    if marans.empty:
        return None
    
    # Grouper par année et calculer l'effectif moyen
    marans['Year'] = marans['Date'].dt.year
    effectif_by_year = marans.groupby('Year').agg({
        'Date': 'count',
        'Ponte_brute': lambda x: x.notna().sum()
    }).reset_index()
    effectif_by_year.columns = ['Année', 'Nombre de jours', 'Jours avec données']
    
    # Ajouter l'effectif théorique
    effectif_by_year['Effectif théorique'] = effectif_by_year['Année'].map({
        2023: 1,
        2024: 3,
        2025: 3
    })
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=effectif_by_year['Année'],
        y=effectif_by_year['Effectif théorique'],
        name='Effectif théorique',
        marker_color='#3498db',
        text=effectif_by_year['Effectif théorique'],
        textposition='auto'
    ))
    
    fig.update_layout(
        title="Effectif MARANS par Année (Gestion Automatique)",
        xaxis_title="Année",
        yaxis_title="Effectif",
        template="plotly_white",
        height=350,
        showlegend=True
    )
    
    return fig

def generate_report():
    print("Génération du rapport de simplification Step 1...")
    
    dfs = load_data()
    
    fig_before, fig_after = create_before_after_sankey()
    fig_reduction = create_data_reduction_viz(dfs)
    fig_effectif = create_effectif_by_year_viz(dfs)
    
    # Statistiques
    nb_lignes_pontes = len(dfs['pontes']) if 'pontes' in dfs else 0
    nb_lignes_marans_indiv = len(dfs['marans_individuels']) if 'marans_individuels' in dfs else 0
    reduction_pct = round((1 - 7306/8770) * 100, 1) if nb_lignes_pontes > 0 else 0
    
    html_content = f"""
    <html>
    <head>
        <title>Simplification Step 1 - Barbara</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f1f4f9;
                margin: 0;
                padding: 0;
            }}
            .header {{
                background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
                color: white;
                padding: 50px 20px;
                text-align: center;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                margin-bottom: 30px;
            }}
            .container {{ max-width: 1400px; }}
            .card {{
                background: white;
                border: none;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.08);
                margin-bottom: 40px;
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
            .stat-value {{ font-size: 2rem; font-weight: 800; color: #27ae60; }}
            .stat-label {{ color: #6c757d; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 1px; }}
            .improvement {{ background: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 15px 0; border-radius: 5px; }}
            .improvement-title {{ font-weight: 700; color: #155724; margin-bottom: 8px; }}
            .badge-benefit {{ background: #27ae60; color: white; padding: 8px 15px; border-radius: 20px; margin: 5px; display: inline-block; }}
            .comparison-container {{ display: flex; gap: 20px; margin: 20px 0; }}
            .before-box {{ flex: 1; background: #fee; border: 2px solid #e74c3c; border-radius: 10px; padding: 20px; }}
            .after-box {{ flex: 1; background: #efe; border: 2px solid #2ecc71; border-radius: 10px; padding: 20px; }}
            .box-title {{ font-weight: 700; font-size: 1.2rem; margin-bottom: 10px; }}
            .before-box .box-title {{ color: #e74c3c; }}
            .after-box .box-title {{ color: #2ecc71; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>✨ Simplification du Pipeline Step 1</h1>
            <p class="lead">Regroupement des Marans dès le début - Élimination des doublons</p>
        </div>
        
        <div class="container pb-5">
            <!-- KPIs -->
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="stat-card">
                        <div class="stat-value">{nb_lignes_pontes}</div>
                        <div class="stat-label">Lignes df_1_pontes</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <div class="stat-value">-{reduction_pct}%</div>
                        <div class="stat-label">Réduction volume</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <div class="stat-value">{nb_lignes_marans_indiv}</div>
                        <div class="stat-label">Données individuelles préservées</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <div class="stat-value">1</div>
                        <div class="stat-label">Fichier éliminé (step2_marans)</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>🎯 Objectif de la Simplification</h2>
                <p>Avant la simplification, le traitement des poules Marans créait des <strong>doublons</strong> et nécessitait une logique complexe répartie sur 3 fichiers. La nouvelle approche regroupe toutes les Marans en un seul groupe <code>MARANS</code> dès le step1, avec un effectif variable selon l'année.</p>
                
                <div class="comparison-container">
                    <div class="before-box">
                        <div class="box-title">❌ Avant</div>
                        <ul>
                            <li>3 niveaux : MARANS_TOTAL, NINA_TINA, individuelles</li>
                            <li>8770 lignes avec doublons</li>
                            <li>Logique répartie sur 3 fichiers</li>
                            <li>Effectif fixe à 3 pour toutes les années</li>
                        </ul>
                    </div>
                    <div class="after-box">
                        <div class="box-title">✅ Après</div>
                        <ul>
                            <li>1 seul groupe : MARANS (unifié)</li>
                            <li>7306 lignes sans doublons</li>
                            <li>Logique centralisée dans step1</li>
                            <li>Effectif variable : 1 (2023), 3 (2024-2025)</li>
                        </ul>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>📊 Visualisation Avant / Après</h2>
                <div class="row">
                    <div class="col-lg-6">
                        {fig_before.to_html(full_html=False, include_plotlyjs='cdn')}
                    </div>
                    <div class="col-lg-6">
                        {fig_after.to_html(full_html=False, include_plotlyjs='cdn')}
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>📉 Impact Quantitatif</h2>
                {fig_reduction.to_html(full_html=False, include_plotlyjs='cdn')}
            </div>

            <div class="card">
                <h2>📅 Gestion Automatique de l'Effectif par Année</h2>
                <p class="text-muted">Le nouveau système calcule automatiquement l'effectif théorique selon l'année, éliminant le besoin de logique manuelle complexe.</p>
                {fig_effectif.to_html(full_html=False, include_plotlyjs='cdn') if fig_effectif else "<p>Données non disponibles</p>"}
            </div>

            <div class="card">
                <h2>🎁 Bénéfices de la Simplification</h2>
                <div class="row">
                    <div class="col-md-6">
                        <div class="improvement">
                            <div class="improvement-title">🚀 Performance</div>
                            <ul>
                                <li>Réduction de 16.7% du volume de données</li>
                                <li>Élimination de 1464 lignes dupliquées</li>
                                <li>Traitement plus rapide</li>
                            </ul>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="improvement">
                            <div class="improvement-title">🧹 Maintenabilité</div>
                            <ul>
                                <li>Logique centralisée dans step1</li>
                                <li>Suppression de step2_marans_specifique.py</li>
                                <li>Code plus simple et lisible</li>
                            </ul>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="improvement">
                            <div class="improvement-title">📊 Qualité des Données</div>
                            <ul>
                                <li>Pas de doublons dans df_1_pontes</li>
                                <li>Effectif variable géré automatiquement</li>
                                <li>1 ligne par date pour MARANS</li>
                            </ul>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="improvement">
                            <div class="improvement-title">🔍 Traçabilité</div>
                            <ul>
                                <li>Données individuelles préservées séparément</li>
                                <li>Information des poules dans Remarques</li>
                                <li>Historique complet conservé</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>📝 Changements Techniques</h2>
                <table class="table table-bordered">
                    <thead class="table-light">
                        <tr>
                            <th>Aspect</th>
                            <th>Avant</th>
                            <th>Après</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>Fonction principale</strong></td>
                            <td><code>format_poules_marans_2_niveaux()</code></td>
                            <td><code>regrouper_marans_simplifie()</code></td>
                        </tr>
                        <tr>
                            <td><strong>Noms de poules</strong></td>
                            <td>MARANS_TOTAL, NINA_TINA, Albertine, Nina, Tina</td>
                            <td>MARANS (unifié)</td>
                        </tr>
                        <tr>
                            <td><strong>Traitement doublons</strong></td>
                            <td>Conservés, traités dans step2_marans</td>
                            <td>Fusionnés par date dans step1</td>
                        </tr>
                        <tr>
                            <td><strong>Fichiers de sortie</strong></td>
                            <td>df_1_pontes.csv (avec doublons)</td>
                            <td>df_1_pontes.csv + df_1_marans_individuels.csv</td>
                        </tr>
                        <tr>
                            <td><strong>Effectif</strong></td>
                            <td>Fixe à 3</td>
                            <td>Variable : 1 (2023), 3 (2024-2025)</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <footer class="text-center py-4 text-muted">
            Généré automatiquement - Simplification Step 1 - {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}
        </footer>
    </body>
    </html>
    """
    
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ Rapport de simplification Step 1 généré : {output_html}")

if __name__ == "__main__":
    generate_report()
