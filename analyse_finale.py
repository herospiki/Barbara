import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import numpy as np

# Configuration
output_html = "final/pontes_finale.html"
input_csv = "final/fichier_final_pontes.csv"

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
    df['Annee_Mois'] = df['Date'].dt.to_period('M').astype(str)
    
    # Type de poule
    df['Type'] = df['Poule_brute'].apply(lambda x: 'Groupe MARANS' if x == 'MARANS' else 'Poule Seule')
    
    return df

def generer_visualisations(df):
    figures = []
    
    # 1. Évolution du taux de ponte mensuel avec marqueurs de décès
    # -----------------------------------------------------------
    mensuel = df.groupby(['Annee_Mois', 'Poule_brute', 'Type']).agg({
        'Ponte': 'sum',
        'Effectif': 'sum'
    }).reset_index()
    
    mensuel['Taux de Ponte (%)'] = 0.0
    mask = mensuel['Effectif'] > 0
    mensuel.loc[mask, 'Taux de Ponte (%)'] = (mensuel.loc[mask, 'Ponte'] / mensuel.loc[mask, 'Effectif'] * 100).round(1)
    
    fig1 = px.line(mensuel, 
                   x='Annee_Mois', 
                   y='Taux de Ponte (%)', 
                   color='Poule_brute',
                   line_dash='Type',
                   title='Évolution du Taux de Ponte Mensuel (%)',
                   labels={'Annee_Mois': 'Mois', 'Poule_brute': 'Poule / Groupe'},
                   markers=True,
                   template="plotly_dark")

    # Identification et ajout des événements de décès
    df_sorted = df.sort_values(['Poule_brute', 'Date']).copy()
    morts = df_sorted[df_sorted.groupby('Poule_brute')['Effectif'].diff() < 0]
    
    
    """ for _, row in morts.iterrows():
        # Annotation sur le graphique mensuel
        fig1.add_vline(x=row['Annee_Mois'], 
                       line_dash="dash", 
                       line_color="red", 
                       opacity=0.6)
        
        fig1.add_annotation(x=row['Annee_Mois'], 
                            y=100,
                            text=f"Décès: {row['Poule_brute']}",
                            showarrow=True,
                            arrowhead=1,
                            ax=0, ay=-30,
                            font=dict(color="red", size=10))
    """
    figures.append(fig1)

    # 2. Total annuel
    # ---------------
    annuel = df.groupby(['Annee', 'Poule_brute', 'Type']).agg({'Ponte': 'sum'}).reset_index()
    # On s'assure que Annee est une chaîne pour l'axe X catégoriel
    annuel['Année'] = annuel['Annee'].astype(str)
    fig2 = px.bar(annuel, x='Année', y='Ponte', color='Poule_brute', barmode='group',\
      title="Production annuelle totale d'œufs", template="plotly_dark")
    fig2.update_layout(legend_title="Poule / Groupe")
    figures.append(fig2)

    # 3. Performance globale
    # ----------------------
    global_stats = df.groupby(['Poule_brute', 'Type']).agg({'Ponte': 'sum', 'Effectif': 'sum'}).reset_index()
    global_stats['Taux_Moyen (%)'] = (global_stats['Ponte'] / global_stats['Effectif'] * 100).round(1)
    global_stats = global_stats.sort_values(by='Taux_Moyen (%)', ascending=False)
    
    fig3 = px.bar(global_stats, x='Poule_brute', y='Taux_Moyen (%)', color='Type',
                  title='Taux de Ponte Moyen Global (%)', template="plotly_dark")
    figures.append(fig3)

    # 4. Saisonnalité (Heatmap)
    # -------------------------
    df['Jour'] = df['Date'].dt.day_name().map({
        'Monday': 'Lun', 'Tuesday': 'Mar', 'Wednesday': 'Mer', 'Thursday': 'Jeu', 'Friday': 'Ven', 'Saturday': 'Sam', 'Sunday': 'Dim'
    })
    
    heat_data = df.groupby(['Jour', 'Mois']).agg({'Ponte': 'sum', 'Effectif': 'sum'}).reset_index()
    heat_data['Taux'] = (heat_data['Ponte'] / heat_data['Effectif'] * 100).round(1)
    
    pivot = heat_data.pivot(index='Jour', columns='Mois', values='Taux')
    pivot = pivot.reindex(['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'])
    
    fig4 = px.imshow(pivot, 
                     title='Saisonnalité : Taux de ponte moyen (%) par jour et mois',
                     labels=dict(x="Mois", y="Jour", color="%"),
                     text_auto=True, 
                     color_continuous_scale='YlGnBu', 
                     template="plotly_dark")
    figures.append(fig4)

    # 5. Chronologie de présence (Gantt)
    # ----------------------------------
    presences = []
    for poule, group in df_sorted.groupby('Poule_brute'):
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
        fig5 = px.timeline(pd.DataFrame(presences), x_start="Début", x_end="Fin", y="Poule", color="Effectif",
                           title="Chronologie de présence des poules", template="plotly_dark")
        fig5.update_yaxes(autorange="reversed")
        figures.append(fig5)

    return figures

def sauvegarder_html(figures):
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write('<html><head><meta charset="utf-8"/><title>Analyse Pontes - Synthese Finale</title>')
        f.write('<style>body{background:#111;color:#eee;font-family:sans-serif;padding:30px;} .chart{margin-bottom:60px;background:#222;padding:20px;border-radius:15px;box-shadow: 0 10px 30px rgba(0,0,0,0.5);}</style></head><body>')
        f.write('<h1 style="text-align:center; color:#ffcc00; margin-bottom:40px;">🐓 Synthèse de l\'Analyse des Pontes</h1>')
        
        for fig in figures:
            f.write('<div class="chart">')
            f.write(fig.to_html(full_html=False, include_plotlyjs="cdn"))
            f.write('</div>')
            
        f.write('</body></html>')
    print(f"✅ Analyse terminée. Rapport généré : {output_html}")

if __name__ == "__main__":
    print("🚀 Démarrage de l'analyse finale...")
    data = charger_donnees()
    if data is not None:
        print(f"📊 Données chargées : {len(data)} lignes.")
        figs = generer_visualisations(data)
        sauvegarder_html(figs)
