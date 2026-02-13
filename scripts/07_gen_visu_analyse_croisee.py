import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Configuration
input_csv = "data/final/pontes_meteo.csv"
output_html = "output/analyse_croisee.html"

def charger_donnees():
    if not os.path.exists(input_csv):
        print(f"Erreur : {input_csv} introuvable.")
        return None
    
    df = pd.read_csv(input_csv, sep=';')
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Remplacer les NaN par 0 pour les calculs, sauf météo
    df['Effectif'] = df['Effectif'].fillna(0)
    df['Nombre_pontes'] = df['Nombre_pontes'].fillna(0)
    
    return df

def calculer_kpis(df):
    # KPI 1: Taux de ponte journalier global
    # On filtre les jours où il y a des poules
    df_active = df[df['Effectif'] > 0].copy()
    
    df_active['Taux_Ponte_%'] = (df_active['Nombre_pontes'] / df_active['Effectif'] * 100).round(1)
    
    return df_active

def generer_visualisations(df):
    figures = []
    explanations = []
    
    # 0. Nuage de points global (Journalier)
    # --------------------------------------
    # On prend chaque jour individuellement
    df_jour = df[df['Effectif'] > 0].copy()
    df_jour['Taux_Ponte_%'] = (df_jour['Nombre_pontes'] / df_jour['Effectif'] * 100).round(1)
    
    fig0 = px.scatter(df_jour, x='T°C (12h-15h)', y='Taux_Ponte_%', 
                      opacity=0.6,
                      title="🌡️ Nuage de Points : Taux de Ponte Journalier vs Température",
                      labels={'T°C (12h-15h)': 'Température (°C)', 'Taux_Ponte_%': 'Taux de Ponte (%)'},
                      hover_data=['Date', 'Effectif', 'Nombre_pontes'],
                      template="plotly_white")
    
    # Ajout d'une ligne de tendance globale (optionnel, mais aide à voir la masse)
    # fig0.add_traces(...) 
    
    figures.append(fig0)
    explanations.append("""
    <div class="explanation">
        <h3>📍 Vue Brute : Tous les points journaliers</h3>
        <p><strong>Lecture :</strong> Chaque point représente une journée. En ordonnée le taux de réussite (ponte %), en abscisse la température.</p>
        <p><strong>Observation :</strong> Ce nuage permet de voir la dispersion réelle des données avant toute agrégation ou lissage. 
        On peut observer si les jours de forte chaleur ou de grand froid correspondent à des points plus bas.</p>
    </div>
    """)

    # 1. Relation Température vs Ponte (Agrégée)
    # ------------------------------------------
    # On agrège par tranche de température pour voir une tendance
    df['Temp_Arrondie'] = df['T°C (12h-15h)'].round(0)
    temp_stats = df.groupby('Temp_Arrondie').agg({
        'Nombre_pontes': 'sum', 
        'Effectif': 'sum',
        'Date': 'count'
    }).reset_index()
    
    temp_stats.rename(columns={'Date': 'Nb_Jours'}, inplace=True)
    
    temp_stats = temp_stats[temp_stats['Effectif'] > 10] # Filtre pour avoir assez de données
    temp_stats['Taux_Ponte_%'] = (temp_stats['Nombre_pontes'] / temp_stats['Effectif'] * 100).round(1)
    
    fig1 = px.scatter(temp_stats, x='Temp_Arrondie', y='Taux_Ponte_%', 
                      size='Nb_Jours',
                      title="📈 Tendance : Taux de Ponte Global par Température (Taille = Nb Jours)",
                      labels={'Temp_Arrondie': 'Température (°C)', 'Taux_Ponte_%': 'Taux de Ponte Global (%)', 'Nb_Jours': 'Nombre de Jours'},
                      hover_data=['Nb_Jours', 'Nombre_pontes'],
                      template="plotly_white")
    figures.append(fig1)
    explanations.append("""
    <div class="explanation">
        <h3>📈 KPI : Tendance Température (Calcul Global)</h3>
        <p><strong>Définition :</strong> Pour chaque température, nous calculons le taux de ponte sur l'ensemble des jours concernés : 
        <code>Somme(Œufs) / Somme(Capacité de ponte)</code>.</p>
        <p><strong>Taille des points :</strong> Plus le point est gros, plus cette température a été observée souvent (nombre de jours). 
        Cela permet de donner plus de poids visuel aux températures fréquentes (zones de confiance) qu'aux extrêmes rares.</p>
        <p><strong>Lecture :</strong> Il ne s'agit pas d'une simple moyenne de pourcentages, mais bien de la performance réelle accumulée à cette température. 
        Cela permet de gommer les variations d'effectif et de voir l'efficacité biologique pure.</p>
    </div>
    """)

    # 2. Production Hebdomadaire & Effectif
    # -------------------------------------
    df['Semaine'] = df['Date'].dt.to_period('W').astype(str)
    
    # Agrégation par semaine
    hebdo = df.groupby('Semaine').agg({
        'Nombre_pontes': 'sum',
        'Effectif': 'mean', # Effectif moyen sur la semaine
        'T°C (12h-15h)': 'mean'
    }).reset_index()
    
    # Calcul du taux de ponte hebdomadaire (Total oeufs / (Moyenne effectif * 7 jours)) * 100
    # Note: On multiplie l'effectif moyen par 7 pour avoir le "nombre de jours-poules" de la semaine
    hebdo['Taux_Ponte_Hebdo_%'] = (hebdo['Nombre_pontes'] / (hebdo['Effectif'] * 7) * 100).round(1)
    
    # Graphique 2 : Total Oeufs vs Effectif
    fig2 = go.Figure()
    
    # Barres pour le nombre d'oeufs
    fig2.add_trace(go.Bar(
        x=hebdo['Semaine'], 
        y=hebdo['Nombre_pontes'], 
        name='Total Œufs',
        marker_color='#FFA726'
    ))
    
    # Ligne pour l'effectif
    fig2.add_trace(go.Scatter(
        x=hebdo['Semaine'], 
        y=hebdo['Effectif'], 
        name='Effectif Moyen',
        yaxis='y2',
        line=dict(color='#66BB6A', width=3, dash='dot')
    ))
    
    fig2.update_layout(
        title="📅 Production Hebdomadaire et Évolution de l'Effectif",
        template="plotly_white",
        yaxis=dict(title="Nombre d'œufs", showgrid=False),
        yaxis2=dict(title="Effectif (Nombre de poules)", overlaying='y', side='right', showgrid=False),
        legend=dict(x=0.01, y=0.99),
        hovermode="x unified"
    )
    figures.append(fig2)
    explanations.append("""
    <div class="explanation">
        <h3>📅 KPI : Production vs Effectif</h3>
        <p><strong>Lecture :</strong> Ce graphique met en regard le volume d'œufs ramassés chaque semaine (barres oranges) avec le nombre de poules présentes (ligne verte en pointillés).</p>
        <p><strong>Intérêt :</strong> Il permet de voir immédiatement si une baisse de production est due à une baisse de forme (barres qui diminuent alors que la ligne reste stable) 
        ou simplement à une baisse de l'effectif (départ ou décès d'une poule).</p>
    </div>
    """)
    
    # Graphique 3 : Taux de Ponte vs Température
    fig3 = go.Figure()

    # Barres pour le Taux de Ponte
    fig3.add_trace(go.Bar(
        x=hebdo['Semaine'], 
        y=hebdo['Taux_Ponte_Hebdo_%'], 
        name='Taux de Ponte (%)',
        marker_color='#42A5F5'
    ))

    # Ligne pour la Température
    fig3.add_trace(go.Scatter(
        x=hebdo['Semaine'], 
        y=hebdo['T°C (12h-15h)'], 
        name='Température Moyenne (°C)',
        yaxis='y2',
        line=dict(color='#FF7043', width=3)
    ))

    fig3.update_layout(
        title="🌡️ Taux de Ponte Hebdomadaire et Température",
        template="plotly_white",
        yaxis=dict(title="Taux de Ponte (%)", showgrid=False, range=[0, 100]),
        yaxis2=dict(title="Température (°C)", overlaying='y', side='right', showgrid=False),
        legend=dict(x=0.01, y=0.99),
        hovermode="x unified"
    )
    figures.append(fig3)
    explanations.append("""
    <div class="explanation">
        <h3>🌡️ KPI : Efficacité de Ponte & Météo</h3>
        <p><strong>Définition :</strong> Le Taux de Ponte Hebdomadaire est calculé en divisant le total des œufs de la semaine par la capacité théorique de ponte (nombre de poules × 7 jours).</p>
        <p><strong>Analyse :</strong> En comparant ce taux (barres bleues) avec la courbe de température (ligne rouge), on peut isoler l'impact du climat sur la performance biologique des poules, 
        indépendamment du nombre de poules présentes.</p>
    </div>
    """)

    return figures, explanations

def sauvegarder_html(figures, explanations):
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write('<html><head><meta charset="utf-8"/><title>Analyse Croisée Météo/Ponte</title>')
        f.write('''<style>
            body { background: #f4f6f8; color: #333; font-family: 'Segoe UI', sans-serif; padding: 20px; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { text-align: center; margin-bottom: 40px; padding: 20px; background: white; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
            h1 { color: #2c3e50; margin: 0; }
            .chart-container { background: white; padding: 20px; margin-bottom: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
            .explanation { background-color: #e8f5e9; border-left: 5px solid #4caf50; padding: 15px; margin-top: 15px; border-radius: 4px; }
            .explanation h3 { margin-top: 0; color: #2e7d32; }
        </style></head><body><div class="container">''')
        
        f.write('''<div class="header">
            <h1>🌦️ Analyse Croisée : Impact Météo & KPIs</h1>
            <p>Exploration des corrélations entre les conditions environnementales et la production d'œufs.</p>
        </div>''')
        
        for i, (fig, expl) in enumerate(zip(figures, explanations)):
            f.write('<div class="chart-container">')
            f.write(fig.to_html(full_html=False, include_plotlyjs="cdn" if i == 0 else False))
            f.write(expl)
            f.write('</div>')
            
        f.write('</div></body></html>')
    print(f"✅ Rapport généré : {output_html}")

if __name__ == "__main__":
    print("🚀 Démarrage de l'analyse croisée...")
    df = charger_donnees()
    if df is not None:
        figs, expls = generer_visualisations(df)
        sauvegarder_html(figs, expls)
