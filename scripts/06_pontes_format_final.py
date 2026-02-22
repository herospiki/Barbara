import pandas as pd
import plotly.express as px
import os
import calendar
import locale
locale.setlocale(locale.LC_TIME, 'French_France.1252')  # Windows

# Charger les données
df_2_pontes = pd.read_csv('data/intermediaire/df_2_pontes.csv', sep=';')
df_2_pontes.fillna({'Remarques': 'RAS'}, inplace=True)

df_final = df_2_pontes[['Date', 'Poule_brute','niveau_observation','Ponte', 'Etat_oeuf', 'Doute', 'Effectif', 'Remarques']].copy()
df_final.rename(columns={'Poule_brute': 'Poule'}, inplace=True)

df_final.to_csv('data/final/pontes_format_final.csv', sep=';', index=False)

# Configuration
output_html = "output/pontes_finale.html"
input_csv = "data/final/pontes_format_final.csv"

def charger_donnees():
    if not os.path.exists(input_csv):
        print(f"Erreur : {input_csv} introuvable.")
        return None
    
    # Lecture brute
    df = pd.read_csv(input_csv, sep=';')
    
    # Conversion forcée
    df['Date'] = pd.to_datetime(df['Date'])
    df['Ponte'] = pd.to_numeric(df['Ponte'], errors='coerce').fillna(0).astype(float)
    df['Effectif'] = pd.to_numeric(df['Effectif'], errors='coerce').fillna(0).astype(float)
    
    # Colonnes temporelles
    df['Annee'] = df['Date'].dt.year
    df['Mois'] = df['Date'].dt.month
    df['Jour'] = df['Date'].dt.day      
    df['Annee_Mois'] = df['Date'].dt.to_period('M').astype(str)
    
    # Type de poule
    df['Type'] = df['Poule'].apply(lambda x: 'Groupe' if x == 'MARANS' else 'Poule Seule')
    
    return df

def generer_visualisations(df):
    figures = []
    explanations = []
    
    # Tri pour la chronologie
    df_sorted = df.sort_values(['Poule', 'Date']).copy()
    
    # 1. Chronologie de présence (Gantt) - EN PREMIER
    # ------------------------------------------------
    presences = []
    for poule, group in df_sorted.groupby('Poule'):
        gp = group[group['Effectif'] > 0].copy()
        if not gp.empty:
            # Détection de segments (changement effectif ou trou > 1 jour)
            gp['seg'] = ((gp['Effectif'].diff().fillna(0) != 0) | (gp['Date'].diff().dt.days.fillna(1) > 1)).cumsum()
            for _, seg_df in gp.groupby('seg'):
                presences.append({
                    'Poule': poule, 
                    'Début': seg_df['Date'].min(), 
                    'Fin': seg_df['Date'].max(),
                    'Effectif': f"Effectif: {int(seg_df['Effectif'].iloc[0])}"
                })
    
    if presences:
        fig1 = px.timeline(pd.DataFrame(presences), x_start="Début", x_end="Fin", y="Poule", color="Effectif",
                           title="📅 Chronologie de Présence des Poules", template="plotly_white")
        fig1.update_yaxes(autorange="reversed")
        figures.append(fig1)
        explanations.append("""
        <div class="explanation">
            <h3>📅 Chronologie de Présence</h3>
            <p>Ce graphique montre les périodes de présence de chaque poule dans le poulailler. 
            Les différentes couleurs indiquent l'effectif (nombre de poules dans le groupe). 
            Les segments séparés indiquent des changements d'effectif ou des interruptions dans les données.</p>
        </div>
        """)
    
    # 2. Évolution du taux de ponte mensuel
    # --------------------------------------
    mensuel = df.groupby(['Annee_Mois', 'Poule', 'Type']).agg({
        'Ponte': 'sum',
        'Effectif': 'sum'
    }).reset_index()
    
    mensuel['Taux de Ponte (%)'] = 0.0
    mask = mensuel['Effectif'] > 0
    mensuel.loc[mask, 'Taux de Ponte (%)'] = (mensuel.loc[mask, 'Ponte'] / mensuel.loc[mask, 'Effectif'] * 100).round(1)
    
    fig2 = px.line(mensuel, 
                   x='Annee_Mois', 
                   y='Taux de Ponte (%)', 
                   color='Poule',
                   line_dash='Type',
                   title='📈 Évolution du Taux de Ponte Mensuel (%)',
                   labels={'Annee_Mois': 'Mois', 'Poule': 'Poule / Groupe'},
                   markers=True,
                   template="plotly_white")
    figures.append(fig2)
    explanations.append("""
    <div class="explanation">
        <h3>📈 Calcul du Taux de Ponte Mensuel</h3>
        <p><strong>Formule :</strong> Taux de Ponte (%) = (Nombre d'œufs pondus / Somme des effectifs) × 100</p>
        <p><strong>Explication :</strong> Pour une poule seule, la <i>somme des effectifs</i> sur un mois correspond à son <strong>nombre de jours de présence</strong> (effectif de 1 par jour).</p>
        <p><strong>Exemple :</strong> Si une poule pond 25 œufs en janvier (31 jours de présence), son taux est : (25 / 31) × 100 = 80.6%</p>
        <p>Pour le groupe MARANS avec un effectif variable (1 en 2023, 3 en 2024-2025), le calcul utilise la somme des effectifs réels de chaque jour du mois.</p>
    </div>
    """)

    # 3. Total annuel
    # ---------------
    annuel = df.groupby(['Annee', 'Poule', 'Type']).agg({'Ponte': 'sum'}).reset_index()
    annuel['Année'] = annuel['Annee'].astype(str)
    fig3 = px.bar(annuel, x='Année', y='Ponte', color='Poule', barmode='group',
                  title="📊 Production Annuelle Totale d'Œufs", template="plotly_white")
    fig3.update_layout(legend_title="Poule / Groupe")
    figures.append(fig3)
    explanations.append("""
    <div class="explanation">
        <h3>📊 Production Annuelle</h3>
        <p>Somme totale des œufs pondus par chaque poule ou groupe sur l'année complète.</p>
    </div>
    """)

    # 4. Performance globale
    # ----------------------
    global_stats = df.groupby(['Poule', 'Type']).agg({'Ponte': 'sum', 'Effectif': 'sum'}).reset_index()
    global_stats['Taux_Moyen (%)'] = (global_stats['Ponte'] / global_stats['Effectif'] * 100).round(1)
    global_stats = global_stats.sort_values(by='Taux_Moyen (%)', ascending=False)
    
    fig4 = px.bar(global_stats, x='Poule', y='Taux_Moyen (%)', color='Type',
                  title='🏆 Taux de Ponte Moyen Global (%)', template="plotly_white")
    figures.append(fig4)
    explanations.append("""
    <div class="explanation">
        <h3>🏆 Calcul du Taux de Ponte Global</h3>
        <p><strong>Formule :</strong> Taux Global (%) = (Total œufs pondus / Somme des effectifs quotidiens) × 100</p>
        <p><strong>Explication :</strong> Pour chaque poule, on additionne tous les œufs pondus sur toute la période, 
        puis on divise par la somme des effectifs de chaque jour de présence.</p>
        <p><strong>Exemple :</strong> Si une poule pond 250 œufs sur 365 jours (effectif = 1 chaque jour), 
        son taux est : (250 / 365) × 100 = 68.5%</p>
        <p>Pour le groupe MARANS avec effectif variable, si on a 100 œufs sur une période où la somme des effectifs 
        quotidiens est de 200 (par ex: 100 jours × 1 poule + 50 jours × 2 poules), le taux est : (100 / 200) × 100 = 50%</p>
    </div>
    """)


    # 5. Saisonnalité (Heatmap)
    # -------------------------

    heat_data = df.groupby(['Jour', 'Mois']).agg({'Ponte': 'sum', 'Effectif': 'sum'}).reset_index()
    heat_data['Taux'] = (heat_data['Ponte'] / heat_data['Effectif'] * 100).round(1)
    
    pivot = heat_data.pivot(index='Mois', columns='Jour', values='Taux')
    pivot.index = pivot.index.map(lambda m: calendar.month_name[m].capitalize())
    
    fig5 = px.imshow(pivot, 
                     title='🌡️ Saisonnalité : Taux de Ponte (%) par Jour et Mois',
                     labels=dict(x="Jour", y="Mois", color="%"),
                     text_auto=True, 
                     color_continuous_scale='YlGnBu', 
                     template="plotly_white")
    figures.append(fig5)
    explanations.append("""
    <div class="explanation">
        <h3>🌡️ Analyse de Saisonnalité</h3>
        <p><strong>Formule :</strong> Taux (%) = (Somme des œufs [Jour + Mois] / Somme des effectifs [Jour + Mois]) × 100</p>
        <p><strong>Explication :</strong> Cette heatmap agrège les données de toute la période (2023-2025) par jour et par mois. 
        Elle permet de voir si les poules sont plus productives à certaines périodes de l'année.</p>
        <p>Comme pour les autres graphiques, l'utilisation de la <strong>somme des effectifs</strong> permet de rapporter la production au nombre réel de poules présentes, 
        garantissant ainsi que les taux sont comparables même si l'effectif a changé au fil des ans.</p>
    </div>
    """)

    return figures, explanations

def sauvegarder_html(figures, explanations):
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write('<html><head><meta charset="utf-8"/><title>Analyse Pontes - Synthèse Finale</title>')
        f.write('''<style>
            body {
                background: #f8f9fa;
                color: #333;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                padding: 30px;
                line-height: 1.6;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px;
                text-align: center;
                border-radius: 15px;
                margin-bottom: 40px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            }
            h1 {
                margin: 0;
                font-size: 2.5rem;
                font-weight: 800;
            }
            .subtitle {
                margin-top: 10px;
                font-size: 1.1rem;
                opacity: 0.9;
            }
            .chart {
                margin-bottom: 50px;
                background: white;
                padding: 25px;
                border-radius: 15px;
                box-shadow: 0 5px 20px rgba(0,0,0,0.08);
            }
            .explanation {
                background: #e3f2fd;
                border-left: 4px solid #2196f3;
                padding: 20px;
                margin: 20px 0;
                border-radius: 8px;
            }
            .explanation h3 {
                color: #1976d2;
                margin-top: 0;
                font-size: 1.3rem;
            }
            .explanation p {
                margin: 10px 0;
            }
            .explanation strong {
                color: #1565c0;
            }
        </style></head><body>''')
        
        f.write('''<div class="header">
            <h1>🐓 Synthèse de l'Analyse des Pontes</h1>
            <p class="subtitle">Visualisation interactive des données de ponte - 2023 à 2025</p>
        </div>''')
        
        for i, (fig, expl) in enumerate(zip(figures, explanations)):
            f.write('<div class="chart">')
            f.write(fig.to_html(full_html=False, include_plotlyjs="cdn" if i == 0 else False))
            f.write(expl)
            f.write('</div>')
            
        f.write('</body></html>')
    print(f"✅ Analyse terminée. Rapport généré : {output_html}")

if __name__ == "__main__":
    print("🚀 Démarrage de l'analyse finale...")
    data = charger_donnees()
    if data is not None:
        print(f"📊 Données chargées : {len(data)} lignes.")
        figs, expls = generer_visualisations(data)
        sauvegarder_html(figs, expls)
