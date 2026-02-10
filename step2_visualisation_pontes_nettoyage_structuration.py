import pandas as pd
import plotly.graph_objects as go
import os

# Configuration
output_html = "interim/step2_visualisation_nettoyage_structuration.html"

def load_data():
    """Charge les données avant et après traitement."""
    df1_path = 'interim/df_1_pontes.csv'
    df2_path = 'interim/df_2_pontes.csv'
    
    if os.path.exists(df1_path) and os.path.exists(df2_path):
        df1 = pd.read_csv(df1_path, sep=';')
        df2 = pd.read_csv(df2_path, sep=';')
        return df1, df2
    return None, None

def create_cleaning_flow_sankey():
    """Visualise le flux de nettoyage de la donnée brute vers la donnée structurée."""
    links = [
        # Source -> Transformation
        ("Ponte_brute", "Analyse Regex & Texte", "Parsing"),
        
        # Transformation -> Attributs structurels
        ("Analyse Regex & Texte", "Ponte", "Calcul entier (n)"),
        ("Analyse Regex & Texte", "Etat_oeuf", "Détections 'c' (cassé)"),
        ("Analyse Regex & Texte", "Doute", "Détecteur '?'"),
        ("Analyse Regex & Texte", "Remarques", "Extraction texte / (m)"),
        ("Analyse Regex & Texte", "Effectif", "Gestion 'dcd' / décès"),
        
        # Attributs -> Résultat final
        ("Ponte", "df_2_pontes_traite", ""),
        ("Etat_oeuf", "df_2_pontes_traite", ""),
        ("Doute", "df_2_pontes_traite", ""),
        ("Remarques", "df_2_pontes_traite", ""),
        ("Effectif", "df_2_pontes_traite", "")
    ]
    
    all_nodes = list(dict.fromkeys([l[0] for l in links] + [l[1] for l in links]))
    node_map = {name: i for i, name in enumerate(all_nodes)}
    
    def get_node_color(name):
        if "df_2" in name: return "#2ecc71"
        if name in ["Analyse Regex & Texte", "Ponte", "Etat_oeuf", "Doute", "Remarques", "Effectif"]: return "#e67e22"
        return "#3498db"

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
          value = [1] * len(links),
          customdata = [l[2] for l in links],
          hovertemplate = '%{source.label} → %{target.label}<br />Action: %{customdata}<extra></extra>'
        ))])

    fig.update_layout(title_text="Flux de Nettoyage : De la notation brute vers les variables typées", font_size=12, height=500)
    return fig

def create_comparison_table(df1, df2):
    """Crée un tableau comparatif avant/après pour illustrer les cas complexes."""
    # On fusionne pour voir le avant/après sur les mêmes lignes
    # Note: On prend un échantillon représentatif de cas complexes
    
    # Cas 1: Notations avec x
    # Cas 2: Notations avec ?
    # Cas 3: Notations avec dcd
    # Cas 4: Notations avec (+)
    
    merged = df2[['Date', 'Poule_brute', 'Ponte_brute', 'Ponte', 'Doute', 'Effectif', 'Remarques']].copy()
    
    complex_cases = merged[
        (merged['Ponte_brute'].str.contains(r'[?cdx\(\)]', na=False)) |
        (merged['Effectif'] == 0)
    ].head(20)
    
    return complex_cases.to_html(classes='table table-bordered table-striped table-hover bg-white', index=False)

def generate_report():
    print("Génération du rapport de structuration (Step 2)...")
    df1, df2 = load_data()
    
    if df1 is None or df2 is None:
        print("Erreur : Fichiers df_1_pontes.csv ou df_2_pontes.csv non trouvés.")
        return

    fig_sankey = create_cleaning_flow_sankey()
    table_comp = create_comparison_table(df1, df2)
    
    # Aperçus simples
    table_df1 = df1.head(10).to_html(classes='table table-sm table-hover bg-white', index=False)
    table_df2 = df2.head(10).to_html(classes='table table-sm table-hover bg-white', index=False)
    
    # KPIs
    total_pontes = df2['Ponte'].sum()
    nb_doutes = df2['Doute'].sum()
    nb_deces = (df2.groupby('Poule_brute')['Effectif'].last() == 0).sum()

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
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🧹 Nettoyage & Structuration des Pontes</h1>
            <p class="lead">Passage des notations brutes (df_1) aux variables quantitatives (df_2)</p>
        </div>
        
        <div class="container pb-5">
            <!-- KPIs -->
            <div class="row mb-4">
                <div class="col-md-4">
                    <div class="stat-card">
                        <div class="stat-value">{int(total_pontes)}</div>
                        <div class="stat-label">Total Œufs (Somme)</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card">
                        <div class="stat-value">{int(nb_doutes)}</div>
                        <div class="stat-label">Notations litigieuses (?)</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card">
                        <div class="stat-value">{nb_deces}</div>
                        <div class="stat-label">Sujets décédés (Effectif 0)</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>📊 Logique de Transformation (Sankey)</h2>
                {fig_sankey.to_html(full_html=False, include_plotlyjs='cdn')}
            </div>

            <div class="card">
                <h2>🔍 Comparaison Avant / Après (Cas Complexes)</h2>
                <div class="table-container">
                    {table_comp}
                </div>
            </div>

            <div class="card">
                <h2>📑 Aperçus Complets</h2>
                <div class="row">
                    <div class="col-lg-6">
                        <p class="preview-title">Tableau Avant (Brut - df_1)</p>
                        <div class="table-container border rounded p-2 bg-light">
                            {table_df1}
                        </div>
                    </div>
                    <div class="col-lg-6">
                        <p class="preview-title">Tableau Après (Nettoyé - df_2)</p>
                        <div class="table-container border rounded p-2 bg-light">
                            {table_df2}
                        </div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>📝 Synthèse du Nettoyage</h2>
                <ul class="list-group list-group-flush">
                    <li class="list-group-item"><b>Mapping des codes :</b> Transformation des 'x', 'x?', 'xx' en entiers calculables.</li>
                    <li class="list-group-item"><b>Propagation des statuts :</b> Une fois qu'une poule est 'dcd', son effectif reste à 0 pour toute la période suivante.</li>
                    <li class="list-group-item"><b>Traitement des Groupes :</b> Gestion des effectifs variables pour les MARANS (passage de 3 à 2 lors des décès reportés).</li>
                    <li class="list-group-item"><b>Extractions secondaires :</b> Isolation des états ('cassé') et des doutes pour filtrage ultérieur.</li>
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
