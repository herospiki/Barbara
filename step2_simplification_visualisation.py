import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# Configuration
output_html = "interim/step2_simplification_visualisation.html"

def load_data():
    """Charge les données finales."""
    final_path = 'final/fichier_final_pontes.csv'
    
    if os.path.exists(final_path):
        df = pd.read_csv(final_path, sep=';')
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
        return df
    return None

def create_workflow_comparison_sankey():
    """Compare le workflow avant et après simplification."""
    # AVANT : 3 fichiers
    links_before = [
        ("df_1_pontes", "step2_nettoyage", "Traitement"),
        ("step2_nettoyage", "df_2_pontes", ""),
        ("df_2_pontes", "Séparation", "Split Marans/Hors Marans"),
        ("Séparation", "df_2_pontes_marans.csv", ""),
        ("Séparation", "df_2_pontes_hors_marans.csv", ""),
        ("df_2_pontes_marans.csv", "step2_marans_specifique", "Regroupement"),
        ("df_2_pontes_hors_marans.csv", "step2_marans_specifique", "Fusion"),
        ("step2_marans_specifique", "fichier_final_pontes.csv", ""),
    ]
    
    all_nodes_before = list(dict.fromkeys([l[0] for l in links_before] + [l[1] for l in links_before]))
    node_map_before = {name: i for i, name in enumerate(all_nodes_before)}
    
    def get_node_color_before(name):
        if "final" in name: return "#2ecc71"  # Vert (Final)
        if "step2_marans" in name: return "#e74c3c"  # Rouge (Fichier supprimé)
        if "Séparation" in name: return "#e67e22"  # Orange (Étape inutile)
        if "df_2" in name and "marans" in name: return "#f39c12"  # Orange clair (Intermédiaire inutile)
        if "step2" in name: return "#3498db"  # Bleu
        return "#95a5a6"  # Gris
    
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
        title_text="❌ AVANT : 3 Fichiers, Logique Fragmentée",
        font_size=11,
        height=450,
        margin=dict(t=60)
    )
    
    # APRÈS : 2 fichiers
    links_after = [
        ("df_1_pontes", "step2_nettoyage", "Traitement direct"),
        ("step2_nettoyage", "Calcul effectif variable", "Par année"),
        ("Calcul effectif variable", "fichier_final_pontes.csv", "Sortie unique"),
    ]
    
    all_nodes_after = list(dict.fromkeys([l[0] for l in links_after] + [l[1] for l in links_after]))
    node_map_after = {name: i for i, name in enumerate(all_nodes_after)}
    
    def get_node_color_after(name):
        if "final" in name: return "#2ecc71"  # Vert (Final)
        if "step2" in name or "Calcul" in name: return "#3498db"  # Bleu
        return "#95a5a6"  # Gris
    
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
        title_text="✅ APRÈS : 2 Fichiers, Logique Unifiée",
        font_size=11,
        height=450,
        margin=dict(t=60)
    )
    
    return fig_before, fig_after

def create_effectif_evolution_viz(df):
    """Visualise l'évolution de l'effectif MARANS avec gestion automatique."""
    if df is None:
        return None
    
    marans = df[df['Poule_brute'] == 'MARANS'].copy()
    
    if marans.empty:
        return None
    
    # Grouper par mois pour visualiser l'évolution
    marans['YearMonth'] = marans['Date'].dt.to_period('M')
    effectif_by_month = marans.groupby('YearMonth')['Effectif'].mean().reset_index()
    effectif_by_month['Date'] = effectif_by_month['YearMonth'].dt.to_timestamp()
    
    fig = go.Figure()
    
    # Ligne de l'effectif
    fig.add_trace(go.Scatter(
        x=effectif_by_month['Date'],
        y=effectif_by_month['Effectif'],
        mode='lines+markers',
        name='Effectif moyen',
        line=dict(color='#3498db', width=3),
        marker=dict(size=8),
        hovertemplate='%{x|%b %Y}<br>Effectif: %{y:.1f}<extra></extra>'
    ))
    
    # Zones colorées par année
    fig.add_vrect(
        x0="2023-01-01", x1="2023-12-31",
        fillcolor="#e74c3c", opacity=0.1,
        layer="below", line_width=0,
        annotation_text="2023: 1 poule", annotation_position="top left"
    )
    
    fig.add_vrect(
        x0="2024-01-01", x1="2024-12-31",
        fillcolor="#f39c12", opacity=0.1,
        layer="below", line_width=0,
        annotation_text="2024: 3 poules", annotation_position="top left"
    )
    
    fig.add_vrect(
        x0="2025-01-01", x1="2025-12-31",
        fillcolor="#2ecc71", opacity=0.1,
        layer="below", line_width=0,
        annotation_text="2025: 3→2 poules", annotation_position="top left"
    )
    
    fig.update_layout(
        title="Évolution de l'Effectif MARANS (Gestion Automatique par Année)",
        xaxis_title="Date",
        yaxis_title="Effectif",
        template="plotly_white",
        height=400,
        hovermode='x unified'
    )
    
    return fig

def create_remarques_distribution_viz(df):
    """Visualise la distribution des remarques avec info des poules."""
    if df is None:
        return None
    
    marans = df[df['Poule_brute'] == 'MARANS'].copy()
    
    if marans.empty:
        return None
    
    # Filtrer les remarques non vides
    remarques = marans[marans['Remarques'].notna() & (marans['Remarques'] != '')]['Remarques'].value_counts().head(15)
    
    if remarques.empty:
        return None
    
    fig = go.Figure(data=[go.Bar(
        x=remarques.index,
        y=remarques.values,
        marker=dict(
            color=remarques.values,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Fréquence")
        ),
        hovertemplate="<b>%{x}</b><br>Occurrences: %{y}<extra></extra>"
    )])
    
    fig.update_layout(
        title="Top 15 des Remarques MARANS (avec info des poules)",
        xaxis_title="Remarque",
        yaxis_title="Nombre d'occurrences",
        template="plotly_white",
        height=450,
        margin=dict(b=150),
        xaxis_tickangle=-45
    )
    
    return fig

def generate_report():
    print("Génération du rapport de simplification Step 2...")
    
    df = load_data()
    
    if df is None:
        print("Erreur : fichier_final_pontes.csv non trouvé.")
        return
    
    fig_before, fig_after = create_workflow_comparison_sankey()
    fig_effectif = create_effectif_evolution_viz(df)
    fig_remarques = create_remarques_distribution_viz(df)
    
    # Statistiques
    total_lignes = len(df)
    nb_marans = len(df[df['Poule_brute'] == 'MARANS'])
    nb_poules = df['Poule_brute'].nunique()
    
    # Effectif par année
    marans = df[df['Poule_brute'] == 'MARANS'].copy()
    marans['Year'] = marans['Date'].dt.year
    effectif_2023 = marans[marans['Year'] == 2023]['Effectif'].mean()
    effectif_2024 = marans[marans['Year'] == 2024]['Effectif'].mean()
    effectif_2025 = marans[marans['Year'] == 2025]['Effectif'].mean()
    
    html_content = f"""
    <html>
    <head>
        <title>Simplification Step 2 - Barbara</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f1f4f9;
                margin: 0;
                padding: 0;
            }}
            .header {{
                background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
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
            h2 {{ color: #3498db; font-weight: 700; margin-bottom: 20px; border-left: 5px solid #3498db; padding-left: 15px; }}
            .stat-card {{
                background: #fff;
                padding: 20px;
                border-radius: 12px;
                text-align: center;
                border-bottom: 4px solid #3498db;
                margin-bottom: 20px;
            }}
            .stat-value {{ font-size: 2rem; font-weight: 800; color: #3498db; }}
            .stat-label {{ color: #6c757d; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 1px; }}
            .improvement {{ background: #d1ecf1; border-left: 4px solid #0c5460; padding: 15px; margin: 15px 0; border-radius: 5px; }}
            .improvement-title {{ font-weight: 700; color: #0c5460; margin-bottom: 8px; }}
            .comparison-container {{ display: flex; gap: 20px; margin: 20px 0; }}
            .before-box {{ flex: 1; background: #fee; border: 2px solid #e74c3c; border-radius: 10px; padding: 20px; }}
            .after-box {{ flex: 1; background: #efe; border: 2px solid #2ecc71; border-radius: 10px; padding: 20px; }}
            .box-title {{ font-weight: 700; font-size: 1.2rem; margin-bottom: 10px; }}
            .before-box .box-title {{ color: #e74c3c; }}
            .after-box .box-title {{ color: #2ecc71; }}
            .code-block {{ background: #f8f9fa; border-left: 4px solid #3498db; padding: 15px; margin: 10px 0; font-family: monospace; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>✨ Simplification du Pipeline Step 2</h1>
            <p class="lead">Gestion automatique de l'effectif - Sortie directe vers fichier final</p>
        </div>
        
        <div class="container pb-5">
            <!-- KPIs -->
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="stat-card">
                        <div class="stat-value">{total_lignes}</div>
                        <div class="stat-label">Lignes totales</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <div class="stat-value">{nb_poules}</div>
                        <div class="stat-label">Poules/Groupes</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <div class="stat-value">{nb_marans}</div>
                        <div class="stat-label">Lignes MARANS</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <div class="stat-value">2</div>
                        <div class="stat-label">Fichiers intermédiaires éliminés</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>🎯 Objectif de la Simplification</h2>
                <p>Avant la simplification, step2 générait 3 fichiers intermédiaires (<code>df_2_pontes.csv</code>, <code>df_2_pontes_marans.csv</code>, <code>df_2_pontes_hors_marans.csv</code>) qui étaient ensuite fusionnés par <code>step2_marans_specifique.py</code>. La nouvelle approche génère directement le fichier final avec gestion automatique de l'effectif variable.</p>
                
                <div class="comparison-container">
                    <div class="before-box">
                        <div class="box-title">❌ Avant</div>
                        <ul>
                            <li>3 fichiers intermédiaires</li>
                            <li>Séparation Marans/Hors Marans</li>
                            <li>Effectif fixe à 3</li>
                            <li>Fusion manuelle dans step2_marans</li>
                            <li>Pas d'info des poules dans Remarques</li>
                        </ul>
                    </div>
                    <div class="after-box">
                        <div class="box-title">✅ Après</div>
                        <ul>
                            <li>1 fichier final direct</li>
                            <li>Pas de séparation nécessaire</li>
                            <li>Effectif variable automatique</li>
                            <li>Pas de fusion manuelle</li>
                            <li>Info des poules ajoutée systématiquement</li>
                        </ul>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>📊 Comparaison du Workflow</h2>
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
                <h2>📅 Gestion Automatique de l'Effectif Variable</h2>
                <p class="text-muted">Le système calcule maintenant automatiquement l'effectif selon l'année, avec propagation du décès en 2025.</p>
                
                <div class="row mb-3">
                    <div class="col-md-4">
                        <div class="stat-card">
                            <div class="stat-value">{effectif_2023:.1f}</div>
                            <div class="stat-label">Effectif moyen 2023</div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="stat-card">
                            <div class="stat-value">{effectif_2024:.1f}</div>
                            <div class="stat-label">Effectif moyen 2024</div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="stat-card">
                            <div class="stat-value">{effectif_2025:.1f}</div>
                            <div class="stat-label">Effectif moyen 2025</div>
                        </div>
                    </div>
                </div>
                
                {fig_effectif.to_html(full_html=False, include_plotlyjs='cdn') if fig_effectif else "<p>Données non disponibles</p>"}
                
                <div class="code-block">
                    <strong>Code simplifié :</strong><br>
                    mask_marans = df_long['Poule_brute'] == 'MARANS'<br>
                    df_long.loc[mask_marans & (df_long['Date'].dt.year == 2023), 'Effectif_theo'] = 1<br>
                    df_long.loc[mask_marans & (df_long['Date'].dt.year == 2024), 'Effectif_theo'] = 3<br>
                    df_long.loc[mask_marans & (df_long['Date'].dt.year == 2025), 'Effectif_theo'] = 3
                </div>
            </div>

            <div class="card">
                <h2>💬 Ajout Systématique de l'Info des Poules</h2>
                <p class="text-muted">La nouvelle fonction <code>traiter_ponte_groupe_marans()</code> ajoute systématiquement l'information des poules dans la colonne Remarques (ex: "Poule(s) : Albertine").</p>
                {fig_remarques.to_html(full_html=False, include_plotlyjs='cdn') if fig_remarques else "<p>Aucune remarque trouvée</p>"}
            </div>

            <div class="card">
                <h2>🎁 Bénéfices de la Simplification</h2>
                <div class="row">
                    <div class="col-md-6">
                        <div class="improvement">
                            <div class="improvement-title">🚀 Efficacité</div>
                            <ul>
                                <li>Sortie directe vers fichier final</li>
                                <li>Élimination de 2 fichiers intermédiaires</li>
                                <li>Pas de séparation/fusion manuelle</li>
                            </ul>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="improvement">
                            <div class="improvement-title">🧹 Simplicité</div>
                            <ul>
                                <li>Fonction dédiée <code>traiter_ponte_groupe_marans()</code></li>
                                <li>Logique centralisée</li>
                                <li>Code plus lisible</li>
                            </ul>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="improvement">
                            <div class="improvement-title">📊 Qualité</div>
                            <ul>
                                <li>Effectif variable géré automatiquement</li>
                                <li>Info des poules toujours présente</li>
                                <li>Propagation du décès correcte</li>
                            </ul>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="improvement">
                            <div class="improvement-title">🔍 Traçabilité</div>
                            <ul>
                                <li>Remarques enrichies automatiquement</li>
                                <li>Historique complet dans un seul fichier</li>
                                <li>Pas de perte d'information</li>
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
                            <td><strong>Fonction groupe</strong></td>
                            <td><code>traiter_ponte_groupe()</code></td>
                            <td><code>traiter_ponte_groupe_marans()</code></td>
                        </tr>
                        <tr>
                            <td><strong>Effectif</strong></td>
                            <td>Fixe à 3 pour tous MARANS</td>
                            <td>Variable : 1 (2023), 3 (2024-2025)</td>
                        </tr>
                        <tr>
                            <td><strong>Remarques</strong></td>
                            <td>Optionnelles</td>
                            <td>Ajoutées systématiquement</td>
                        </tr>
                        <tr>
                            <td><strong>Fichiers intermédiaires</strong></td>
                            <td>df_2_pontes_marans.csv + df_2_pontes_hors_marans.csv</td>
                            <td>Aucun (sortie directe)</td>
                        </tr>
                        <tr>
                            <td><strong>Fichier final</strong></td>
                            <td>Généré par step2_marans_specifique.py</td>
                            <td>Généré directement par step2</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <footer class="text-center py-4 text-muted">
            Généré automatiquement - Simplification Step 2 - {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}
        </footer>
    </body>
    </html>
    """
    
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ Rapport de simplification Step 2 généré : {output_html}")

if __name__ == "__main__":
    generate_report()
