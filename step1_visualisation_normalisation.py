import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# Configuration
output_html = "interim/step1_visualisation_normalisation.html"

def load_data():
    """Charge les fichiers df_1 depuis le dossier interim."""
    files = {
        'meteo': 'interim/df_1_meteo.csv',
        'pontes': 'interim/df_1_pontes.csv',
        'commentaires': 'interim/df_1_commentaires.csv'
    }
    dfs = {}
    for key, path in files.items():
        if os.path.exists(path):
            # Tous utilisent ';' comme séparateur d'après les aperçus
            df = pd.read_csv(path, sep=';')
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
            dfs[key] = df
    return dfs

def create_structural_evolution_viz():
    """Crée une visualisation détaillée de la transformation structurelle."""
    # Mapping multi-étapes
    links = [
        # --- ÉTAPE 1 : Sources -> Transformations Initiales ---
        ("Pluie", "Pluie(mm)", "Normalisation"),
        ("T°C (12-15h)", "T°C (12h-15h)", "Normalisation"),
        ("3 Marans", "Marans", "Consolidation"),
        ("Date", "Date (index)", "Identifiant"),
        
        # --- ÉTAPE 2 : Transformations -> Enrichissement / Structuration ---
        ("Météo", "df_1_meteo", "Conservation"),
        ("Pluie(mm)", "df_1_meteo", "Conservation"),
        ("T°C (12h-15h)", "df_1_meteo", "Conservation"),
        ("Humidité", "df_1_meteo", "Conservation"),
        
        ("Commentaires", "df_1_commentaires", "Conservation"),
        ("œuf trouvé/t. trouvaille", "df_1_commentaires", "Conservation"),
        
        # Le cœur de la transformation Poules
        ("Poules (Toutes)", "Dépivotage (Melt)", "Format Long"),
        ("Marans", "Dépivotage (Melt)", "Format Long"),
        
        ("Dépivotage (Melt)", "Enrichissement (Metadata)", "Logique Métier"),
        
        # --- ÉTAPE 3 : Enrichissement -> Attributs Finaux ---
        ("Enrichissement (Metadata)", "niveau_observation", "Assignation Niveau (ind / grpe)"),
        ("Enrichissement (Metadata)", "group_id", "Assignation MARANS"),
        ("Enrichissement (Metadata)", "Poule_brute", "Extraction"),
        ("Enrichissement (Metadata)", "Ponte_brute", "Extraction"),
        
        # --- ÉTAPE 4 : Attributs -> Fichiers Finaux ---
        ("Date (index)", "df_1_meteo", ""),
        ("Date (index)", "df_1_commentaires", ""),
        ("Date (index)", "df_1_pontes", ""),
        
        ("niveau_observation", "df_1_pontes", ""),
        ("group_id", "df_1_pontes", ""),
        ("Poule_brute", "df_1_pontes", ""),
        ("Ponte_brute", "df_1_pontes", ""),
        
        # Suppressions
        ("T°C nuit", "Filtré / Supprimé", "Nettoyage"),
        ("T°C poulailler", "Filtré / Supprimé", "Nettoyage")
    ]
    
    all_nodes = list(dict.fromkeys([l[0] for l in links] + [l[1] for l in links]))
    node_map = {name: i for i, name in enumerate(all_nodes)}
    
    # Couleurs
    def get_node_color(name):
        if "df_1" in name: return "#2ecc71"  # Vert (Cibles)
        if "Metadata" in name or "niveau" in name or "group_id" in name: return "#f1c40f" # Jaune (Enrichissement)
        if "Melt" in name or "Normalisation" in name: return "#e67e22" # Orange (Transfo)
        if "Supprimé" in name: return "#e74c3c" # Rouge
        return "#3498db" # Bleu (Sources)

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

    fig.update_layout(title_text="Détail du flux structurel (Focus : Structuration des donnée de Pontes)", font_size=12, height=700)
    return fig

def create_summary_table():
    """Crée un tableau récapitulatif des changements majeurs."""
    changes = {
        "Type de changement": [
            "Normalisation noms", 
            "Traitement Poules", 
            "Extraction Météo", 
            "Enrichissement",
            "Filtrage"
        ],
        "Description": [
            "Renommage des colonnes Pluie et Température pour uniformité sur 3 ans.",
            "Passage d'un format large (1 col par poule) à un format long (1 ligne par observation).",
            "Isolation des variables climatiques pour analyse environnementale.",
            "Ajout des colonnes 'niveau_observation' (individuel/groupe) et 'group_id'.",
            "Suppression des colonnes techniques non systématiques (T°C nuit, etc.)."
        ],
        "Impact": [
            "Cohérence temporelle",
            "Simplification des calculs",
            "Modularité des données",
            "Analyses multi-niveaux",
            "Réduction du bruit"
        ]
    }
    return pd.DataFrame(changes).to_html(classes='table table-bordered table-striped', index=False)

def generate_report():
    print("Génération du rapport d'évolution structurelle...")
    
    fig_sankey = create_structural_evolution_viz()
    table_summary = create_summary_table()
    
    # On garde aussi l'aperçu des fichiers df_1_...
    dfs = load_data()
    
    html_content = f"""
    <html>
    <head>
        <title>Normalisation des Données - Barbara</title>
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
            .step-title {{ font-size: 1.1rem; font-weight: 700; color: #1e3c72; margin-top: 15px; margin-bottom: 10px; }}
            .table-container {{ overflow-x: auto; }}
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
            small {{ color: #6c757d; display: block; margin-bottom: 8px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🛠️ Normalisation & Formatage des Données</h1>
            <p class="lead">Passage des fichiers bruts vers le format structuré "Interim" (df_1)</p>
        </div>
        
        <div class="container pb-5">
            <!-- KPIs de Structure -->
            <div class="row mb-4">
                <div class="col-md-4">
                    <div class="stat-card">
                        <div class="stat-value">3</div>
                        <div class="stat-label">Fichiers de sortie (df_1)</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card">
                        <div class="stat-value">Format Long</div>
                        <div class="stat-label">Structure des Pontes</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card">
                        <div class="stat-value">Normalisé</div>
                        <div class="stat-label">État des colonnes</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>📊 Flow de Transformation Structurelle</h2>
                <p class="text-muted">Visualisation détaillée du passage des colonnes d'origine vers les nouveaux attributs enrichis.</p>
                {fig_sankey.to_html(full_html=False, include_plotlyjs='cdn')}
            </div>

            <div class="card">
                <h2>📝 Synthèse des Changements</h2>
                <div class="table-container">
                    {table_summary}
                </div>
            </div>

            <div class="card">
                <h2>📑 Aperçu des Données (Fichiers Interim)</h2>
                <div class="row">
                    <div class="col-lg-4 mb-4">
                        <div class="p-2 border rounded bg-light">
                            <p class="step-title">1. Pontes (Long Format)</p>
                            <small>Colonnes enrichies (niveau, group_id)</small>
                            <div class="table-responsive">
                                {dfs['pontes'].head(8).to_html(classes='table table-sm table-hover bg-white', index=False)}
                            </div>
                        </div>
                    </div>
                    <div class="col-lg-4 mb-4">
                        <div class="p-2 border rounded bg-light">
                            <p class="step-title">2. Météo Clean</p>
                            <small>Colonnes renommées et filtrées</small>
                            <div class="table-responsive">
                                {dfs['meteo'].head(8).to_html(classes='table table-sm table-hover bg-white', index=False)}
                            </div>
                        </div>
                    </div>
                    <div class="col-lg-4 mb-4">
                        <div class="p-2 border rounded bg-light">
                            <p class="step-title">3. Commentaires</p>
                            <small>Journal d'observations textuelles</small>
                            <div class="table-responsive">
                                {dfs['commentaires'].dropna(subset=['Commentaires']).head(8).to_html(classes='table table-sm table-hover bg-white', index=False)}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <footer class="text-center py-4 text-muted">
            Généré automatiquement par Antigravity - Normalisation Audit {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}
        </footer>
    </body>
    </html>
    """
    
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ Rapport structurel (Look & Feel Audit) généré : {output_html}")


if __name__ == "__main__":
    generate_report()
