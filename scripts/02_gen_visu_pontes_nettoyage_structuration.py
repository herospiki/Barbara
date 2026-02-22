import pandas as pd
import plotly.graph_objects as go
import os

# Configuration
output_html = "output/step2_visualisation_nettoyage_structuration.html"

def load_data():
    """Charge les données avant et après traitement."""
    df1_path = 'data/intermediaire/df_1_pontes.csv'
    df2_path = 'data/intermediaire/df_2_pontes.csv'
    
    data = {}
    if os.path.exists(df1_path): 
        data['df1'] = pd.read_csv(df1_path, sep=';')
        
    if os.path.exists(df2_path): 
        df2 = pd.read_csv(df2_path, sep=';')
        data['df2'] = df2
        
        # Dérivation des sous-ensembles
        data['df_marans'] = df2[df2['Poule_brute'] == 'MARANS'].copy()
        data['df_hors_marans'] = df2[df2['Poule_brute'] != 'MARANS'].copy()
    else:
        data['df2'] = None
        data['df_marans'] = None
        data['df_hors_marans'] = None

    return data.get('df1'), data.get('df2'), data.get('df_marans'), data.get('df_hors_marans')

def create_cleaning_flow_sankey():
    """Visualise le flux de nettoyage de la donnée brute vers la donnée structurée."""
    links = [
        # --- Sources ---
        ("Ponte_brute", "Analyse Regex & Texte", "Parsing"),
        ("niveau_observation", "Effectif", "Effectif théorique (1/2/3/4)"),
        ("Poule_brute", "Effectif", "Init Marans/Nina-Tina"),
        
        # --- Transformations ---
        ("Analyse Regex & Texte", "Ponte", "Calcul entier (n)"),
        ("Analyse Regex & Texte", "Etat_oeuf", "Détections 'c' (cassé)"),
        ("Analyse Regex & Texte", "Doute", "Détecteur '?'"),
        ("Analyse Regex & Texte", "Remarques", "Extraction texte / (m)"),
        ("Analyse Regex & Texte", "Effectif", "Ajustement si 'dcd'"),
        
        # --- Cibles Intermédiaires ---
        ("Ponte", "df_2_pontes", ""),
        ("Etat_oeuf", "df_2_pontes", ""),
        ("Doute", "df_2_pontes", ""),
        ("Remarques", "df_2_pontes", ""),
        ("Effectif", "df_2_pontes", "")
    ]
    
    all_nodes = list(dict.fromkeys([l[0] for l in links] + [l[1] for l in links]))
    node_map = {name: i for i, name in enumerate(all_nodes)}
    
    def get_node_color(name):
        if name == "df_2_pontes": return "#2ecc71"  # Vert (Cible)
        if name in ["Analyse Regex & Texte", "Ponte", "Etat_oeuf", "Doute", "Remarques", "Effectif"]: 
            return "#f39c12" # Orange (Attributs/Transfo)
        return "#3498db" # Bleu (Source)

    fig = go.Figure(data=[go.Sankey(
        node = dict(
          pad = 15, thickness = 20,
          line = dict(color = "black", width = 0.5),
          label = all_nodes,
          color = [get_node_color(n) for n in all_nodes]
        ),
        link = dict(
          source = [node_map[l[0]] for l in links],
          target = [node_map[l[1]] for l in links],
          value = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0.5, 0.5], # Ajustement visuel
          customdata = [l[2] for l in links],
          hovertemplate = '%{source.label} → %{target.label}<br />Action: %{customdata}<extra></extra>'
        ))])

    fig.update_layout(title_text="Flux de Nettoyage et Séparation des Groupes", font_size=12, height=500)
    return fig



def create_categorical_distribution_viz(df, column, title, color):
    """Crée un graphique à barres pour la distribution d'une variable catégorielle."""
    if df is None or column not in df.columns:
        return None
    
    # Nettoyage pour les remarques (on enlève les vides)
    dist = df[df[column].notna() & (df[column] != '') & (df[column] != 'RAS')]
    if column == 'Remarques':
        # On peut avoir beaucoup de remarques uniques, on prend les plus fréquentes
        dist = dist[column].value_counts().head(15).reset_index()
    else:
        dist = dist[column].value_counts().reset_index()
        
    dist.columns = [column, 'Count']
    
    fig = go.Figure(data=[go.Bar(
        x=dist[column],
        y=dist['Count'],
        marker_color=color,
        hovertemplate="<b>%{x}</b><br>Occurrences: %{y}<extra></extra>"
    )])
    
    fig.update_layout(
        title=title,
        xaxis_title=column,
        yaxis_title="Nombre",
        template="plotly_white",
        height=400,
        margin=dict(t=50, b=100)
    )
    return fig


def generate_report():
    print("Génération du rapport de structuration (Step 2)...")
    df1, df2, df_marans, df_hors_marans = load_data()
    
    if df1 is None or df2 is None:
        print("Erreur : Fichiers df_1_pontes.csv ou df_2_pontes.csv non trouvés.")
        return

    fig_sankey = create_cleaning_flow_sankey()
    # table_comp = create_comparison_table(df1, df2)
    
    # Nouvelles visualisations : État et Remarques
    fig_etat = create_categorical_distribution_viz(df2, 'Etat_oeuf', "Distribution de 'Etat_oeuf' (Hors RAS)", "#e74c3c")
    fig_remarques = create_categorical_distribution_viz(df2, 'Remarques', "Top 15 des Remarques extraites", "#3498db")
    
    # Aperçus simples
    table_df1 = df1.head(10).to_html(classes='table table-sm table-hover bg-white', index=False)
    table_df2 = df2.head(10).to_html(classes='table table-sm table-hover bg-white', index=False)
    
    # KPIs
    total_pontes = df2['Ponte'].sum()
    nb_doutes = df2['Doute'].sum()
    nb_deces = (df2.groupby('Poule_brute')['Effectif'].last() == 0).sum()

    # Infos Groupes
    marans_list = df_marans['Poule_brute'].unique().tolist() if df_marans is not None else []
    hors_marans_list = df_hors_marans['Poule_brute'].unique().tolist() if df_hors_marans is not None else []
    
    eggs_hors_marans = df_hors_marans['Ponte'].sum() if df_hors_marans is not None else 0

    # Aperçus Spécifiques
    table_marans = df_marans.sort_values(by='Date', ascending=True).tail(15).to_html(classes='table table-sm table-hover bg-white', index=False) if df_marans is not None else ""
    table_hors_marans = df_hors_marans.sort_values(by='Date', ascending=True).tail(15).to_html(classes='table table-sm table-hover bg-white', index=False) if df_hors_marans is not None else ""

    html_content = f"""
    <html>
    <head>
        <title>Nettoyage & Structuration - Barbara</title>
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
            .preview-title {{ font-size: 1.1rem; font-weight: 700; color: #1e3c72; margin-top: 15px; }}
            .badge-group {{ margin: 2px; font-size: 0.9rem; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🧹 Nettoyage & Structuration du fichier de Pontes</h1>
            <p class="lead">Passage des notations brutes (df_1) aux variables quantitatives (df_2)</p>
             <p class="lead"> Traitement du cas des poules Marans (groupe) </p>
        </div>
        
        <div class="container pb-5">
            <!-- KPIs -->
            <div class="row mb-4">
                <div class="col-md-4">
                    <div class="stat-card">
                        <div class="stat-value">{int(eggs_hors_marans)}</div>
                        <div class="stat-label">Œufs Validés (Hors Marans)</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card">
                        <div class="stat-value">{len(df_marans) if df_marans is not None else 0}</div>
                        <div class="stat-label">Volume de données Marans</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card">
                        <div class="stat-value">{int(nb_doutes)}</div>
                        <div class="stat-label">Alertes Qualité (?)</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>📊 Logique de Transformation & Séparation</h2>
                <div class="row">
                    <div class="col-lg-9">
                        {fig_sankey.to_html(full_html=False, include_plotlyjs='cdn')}
                    </div>
                    <div class="col-lg-3">
                        <div class="mt-4">
                            <h5>🕊️ Groupe Marans</h5>
                            <p class="text-muted small">Suivi spécifique pour les poules historiques et les récoltes groupées. <i>(Données consolidées : l'addition des pontes est désormais fiable)</i></p>
                            <div>
                                {' '.join([f'<span class="badge bg-primary badge-group">{p}</span>' for p in marans_list])}
                            </div>
                            <hr>
                            <h5>🐔 Hors Marans</h5>
                            <p class="text-muted small">Autres colonies et individus suivis séparément.</p>
                            <div>
                                {' '.join([f'<span class="badge bg-secondary badge-group">{p}</span>' for p in hors_marans_list])}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <h2>🥚 État des Œufs</h2>
                        {fig_etat.to_html(full_html=False, include_plotlyjs='cdn') if fig_etat else "<p>Aucune anomalie détectée.</p>"}
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <h2>💬 Analyse des Remarques</h2>
                        {fig_remarques.to_html(full_html=False, include_plotlyjs='cdn') if fig_remarques else "<p>Aucune remarque trouvée.</p>"}
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>📁 Résultat : Fichier Unique Structuré</h2>
                <div class="text-center p-4">
                    <div class="p-3 border rounded bg-white" style="border-left: 5px solid #2ecc71 !important;">
                        <h4 class="text-success">df_2_pontes.csv</h4>
                        <div class="display-6 fw-bold">{len(df2) if df2 is not None else 0}</div>
                        <div class="text-muted">Total Lignes Traitées</div>
                        <div class="mt-3">
                            <span class="badge bg-primary me-2">Dont Marans : {len(df_marans) if df_marans is not None else 0}</span>
                            <span class="badge bg-secondary">Dont Hors Marans : {len(df_hors_marans) if df_hors_marans is not None else 0}</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>📑 Comparaison Avant / Après (df_1 vs df_2)</h2>
                <div class="row">
                    <div class="col-lg-6">
                        <p class="preview-title">Source (df_1_pontes.csv)</p>
                        <div class="table-container border rounded p-2 bg-light">
                            {table_df1}
                        </div>
                    </div>
                    <div class="col-lg-6">
                        <p class="preview-title">Résultat Structuré (df_2_pontes.csv)</p>
                        <div class="table-container border rounded p-2 bg-light">
                            {table_df2}
                        </div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>📝 Synthèse du Nettoyage & Structuration</h2>
                <ul class="list-group list-group-flush">
                    <li class="list-group-item"><b>Mapping des codes :</b> Transformation des notations complexes ('x', 'x?', 'xx', '(+1)') en valeurs entières calculables pour l'analyse statistique.</li>
                    <li class="list-group-item"><b>Consolidation Marans :</b> Regroupement de toutes les observations (individuelles et groupées) sous une entité unique, permettant une <b>somme directe fiable</b> de la production.</li>
                    <li class="list-group-item"><b>Dynamique des Effectifs :</b> Calcul de l'effectif présent (1, 2, 3) avec <b>propagation automatique du statut 'décédée'</b> pour garantir la cohérence des taux de ponte futurs.</li>
                    <li class="list-group-item"><b>Structuration Granulaire :</b> Extraction systématique des états de l'œuf (cassé) et des doutes de saisie dans des colonnes dédiées pour un filtrage précis.</li>
                    <li class="list-group-item"><b>Séparation Analytique :</b> Intégration dans un fichier unique avec distinction claire (via <code>group_id</code>) permettant d'analyser d'un côté la production propre (Hors Marans) et de l'autre le comportement complexe de la colonie Marans.</li>
                </ul>
            </div>
        </div>
        
        <footer class="text-center py-4 text-muted border-top">
            Généré automatiquement par Antigravity - Structuration Step 2 - {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}
        </footer>
    </body>
    </html>
    """
    
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ Rapport de structuration (avec aperçus) généré : {output_html}")

if __name__ == "__main__":
    generate_report()

