import pandas as pd
import numpy as np
import os

# ===========================================================================
# CONFIGURATION
# ===========================================================================
input_csv   = "data/intermediaire/df_3_meteo.csv"
input_histo = "data/raw/Histo_Meteo.xlsx"
sheet_histo = "Histo_Meteo"   # Colonnes : Date_Heure, Temp_C, Humidite_pct, Pluie_mm, THI
output_html = "output/check_meteo.html"

seuil_t = 5    # °C — seuil d'alerte écart température
seuil_p = 10   # mm — seuil d'alerte écart précipitations
seuil_h = 20   # % — seuil d'alerte écart humidité

# ===========================================================================
# 1. CHARGEMENT DES DONNÉES
# ===========================================================================
print("📂 Chargement du CSV df_3_meteo.csv...")
df_csv = pd.read_csv(input_csv, sep=';', parse_dates=['Date'])
df_csv['Date'] = df_csv['Date'].dt.normalize()
print(f"   {len(df_csv)} jours | {df_csv['Date'].min().date()} → {df_csv['Date'].max().date()}")

print(f"📂 Chargement de la feuille '{sheet_histo}' du XLSX...")
df_histo = pd.read_excel(input_histo, sheet_name=sheet_histo, parse_dates=['Date_Heure'])
print(f"   {len(df_histo)} lignes horaires | {df_histo['Date_Heure'].min()} → {df_histo['Date_Heure'].max()}")

# ===========================================================================
# 2. AGRÉGATION JOURNALIÈRE DU XLSX HORAIRE
# ===========================================================================
print("🔄 Agrégation journalière du XLSX (horaire → jour)...")
df_histo['Date'] = df_histo['Date_Heure'].dt.normalize()

df_histo_jour = df_histo.groupby('Date').agg(
    Histo_Temp_moy  = ('Temp_C',       'mean'),
    Histo_Temp_max  = ('Temp_C',       'max'),
    Histo_Temp_min  = ('Temp_C',       'min'),
    Histo_Hum_moy   = ('Humidite_pct', 'mean'),
    Histo_Hum_min   = ('Humidite_pct', 'min'),
    Histo_Hum_max   = ('Humidite_pct', 'max'),
    Histo_Pluie_sum = ('Pluie_mm',     'sum'),
    Histo_THI_moy   = ('THI',          'mean'),
    Histo_THI_max   = ('THI',          'max'),
).reset_index()

# Arrondi
for col in df_histo_jour.columns[1:]:
    df_histo_jour[col] = df_histo_jour[col].round(2)

print(f"   {len(df_histo_jour)} jours agrégés | {df_histo_jour['Date'].min().date()} → {df_histo_jour['Date'].max().date()}")

# ===========================================================================
# 3. FUSION ET COMPARAISON
# ===========================================================================
print("🔗 Fusion des deux sources sur la Date...")
cols_csv = ['Date', 'Pluie(mm)', 'T°C (12h-15h)', 'Humidité']
cols_csv_dispo = [c for c in cols_csv if c in df_csv.columns]
df_comp = df_csv[cols_csv_dispo].merge(df_histo_jour, on='Date', how='inner')
print(f"   {len(df_comp)} jours en commun | {df_comp['Date'].min().date()} → {df_comp['Date'].max().date()}")

# ===========================================================================
# 4. MÉTRIQUES DE COHÉRENCE
# ===========================================================================
print("📊 Calcul des métriques...")

resultats = []

def metriques(s1, s2, label, seuil=None):
    diff = (s1 - s2).abs()
    n = int(diff.notna().sum())
    pct = round((diff > seuil).sum() / n * 100, 1) if seuil is not None and n > 0 else None
    return {
        'Comparaison': label,
        'MAE': round(diff.mean(), 2),
        'RMSE': round(np.sqrt((diff**2).mean()), 2),
        'Max écart': round(diff.max(), 2),
        'Corrélation': round(s1.corr(s2), 3),
        f'% > seuil': pct,
        'Nb jours': n
    }

# Température CSV (12-15h) — meilleure correspondance avec Temp_max ou Temp_moy ?
if 'T°C (12h-15h)' in df_comp.columns:
    resultats.append(metriques(df_comp['T°C (12h-15h)'], df_comp['Histo_Temp_moy'],
                               'T°C CSV (12-15h) vs Histo T°C moyenne journalière', seuil=seuil_t))
    resultats.append(metriques(df_comp['T°C (12h-15h)'], df_comp['Histo_Temp_max'],
                               'T°C CSV (12-15h) vs Histo T°C max journalier', seuil=seuil_t))

# Pluie
if 'Pluie(mm)' in df_comp.columns:
    resultats.append(metriques(df_comp['Pluie(mm)'], df_comp['Histo_Pluie_sum'],
                               'Pluie(mm) CSV vs Histo Pluie somme journalière', seuil=seuil_p))

# Humidité (CSV en [0,1] → convertir en %)
if 'Humidité' in df_comp.columns:
    h_csv = df_comp['Humidité'] * 100 if df_comp['Humidité'].median() < 2 else df_comp['Humidité']
    resultats.append(metriques(h_csv, df_comp['Histo_Hum_moy'],
                               'Humidité CSV (%) vs Histo Humidité moyenne journalière (%)', seuil=seuil_h))
    resultats.append(metriques(h_csv, df_comp['Histo_Hum_max'],
                               'Humidité CSV (%) vs Histo Humidité max journalière (%)', seuil=seuil_h))
    resultats.append(metriques(h_csv, df_comp['Histo_Hum_min'],
                               'Humidité CSV (%) vs Histo Humidité min journalière (%)', seuil=seuil_h))

df_resultats = pd.DataFrame(resultats)
print("\n" + df_resultats.to_string(index=False))

# ===========================================================================
# 5. JOURS ABERRANTS
# ===========================================================================
if 'T°C (12h-15h)' in df_comp.columns:
    df_comp['ecart_T'] = (df_comp['T°C (12h-15h)'] - df_comp['Histo_Temp_max']).abs()
    aberrants_t = df_comp[df_comp['ecart_T'] > seuil_t][
        ['Date', 'T°C (12h-15h)', 'Histo_Temp_max', 'ecart_T']
    ].copy()

if 'Pluie(mm)' in df_comp.columns:
    df_comp['ecart_P'] = (df_comp['Pluie(mm)'] - df_comp['Histo_Pluie_sum']).abs()
    aberrants_p = df_comp[df_comp['ecart_P'] > seuil_p][
        ['Date', 'Pluie(mm)', 'Histo_Pluie_sum', 'ecart_P']
    ].copy()

print(f"\n⚠️  Jours avec écart T > {seuil_t}°C : {len(aberrants_t)}")
print(aberrants_t.to_string(index=False) if not aberrants_t.empty else "   → Aucun")
print(f"\n⚠️  Jours avec écart Pluie > {seuil_p}mm : {len(aberrants_p)}")
print(aberrants_p.to_string(index=False) if not aberrants_p.empty else "   → Aucun")

# ===========================================================================
# 6. EXPORT HTML INTERACTIF
# ===========================================================================
import plotly.graph_objects as go

os.makedirs(os.path.dirname(output_html), exist_ok=True)
figs_html = []

# Graphique 1 : Température
fig_t = go.Figure()
if 'T°C (12h-15h)' in df_comp.columns:
    fig_t.add_trace(go.Scatter(x=df_comp['Date'], y=df_comp['T°C (12h-15h)'],
                               name='CSV (relevé 12h-15h)', line=dict(color='#e74c3c', width=2)))
fig_t.add_trace(go.Scatter(x=df_comp['Date'], y=df_comp['Histo_Temp_moy'],
                           name='Histo moyenne journalière', line=dict(color='#3498db', width=2, dash='dot')))
fig_t.add_trace(go.Scatter(x=df_comp['Date'], y=df_comp['Histo_Temp_max'],
                           name='Histo max journalier', line=dict(color='#e67e22', width=1, dash='dash')))
fig_t.add_trace(go.Scatter(x=df_comp['Date'], y=df_comp['Histo_Temp_min'],
                           name='Histo min journalier', line=dict(color='#95a5a6', width=1, dash='dash')))
fig_t.update_layout(title='🌡️ Comparaison Température', xaxis_title='Date', yaxis_title='T°C',
                    template='plotly_white', legend=dict(orientation='h', y=-0.25))
figs_html.append(('🌡️ Température', fig_t,
    "Le relevé CSV est effectué entre 12h et 15h, il devrait être proche du <b>maximum journalier</b> (courbe orange). "
    "Un bon alignement valide la cohérence des deux sources."))

# Graphique 2 : Pluie
fig_p = go.Figure()
if 'Pluie(mm)' in df_comp.columns:
    fig_p.add_trace(go.Bar(x=df_comp['Date'], y=df_comp['Pluie(mm)'],
                           name='CSV Pluie(mm)', marker_color='#3498db', opacity=0.8))
fig_p.add_trace(go.Bar(x=df_comp['Date'], y=df_comp['Histo_Pluie_sum'],
                       name='Histo Pluie somme (mm)', marker_color='#e74c3c', opacity=0.6))
fig_p.update_layout(title='🌧️ Comparaison Précipitations', xaxis_title='Date', yaxis_title='mm',
                    barmode='overlay', template='plotly_white', legend=dict(orientation='h', y=-0.25))
figs_html.append(('🌧️ Précipitations', fig_p,
    "Le CSV note la pluie le matin à 8h avec un léger décalage temporel (cf. notes méthodologiques). "
    "Des écarts ponctuels entre les deux sources sont donc normaux."))

# Graphique 3 : Humidité
if 'Humidité' in df_comp.columns:
    h_csv_plot = df_comp['Humidité'] * 100 if df_comp['Humidité'].median() < 2 else df_comp['Humidité']
    fig_h = go.Figure()
    fig_h.add_trace(go.Scatter(x=df_comp['Date'], y=h_csv_plot,
                               name='CSV Humidité (%)', line=dict(color='#2ecc71', width=2)))
    fig_h.add_trace(go.Scatter(x=df_comp['Date'], y=df_comp['Histo_Hum_moy'],
                               name='Histo Humidité moy. (%)', line=dict(color='#9b59b6', width=2, dash='dot')))
    fig_h.add_trace(go.Scatter(x=df_comp['Date'], y=df_comp['Histo_Hum_max'],
                               name='Histo Humidité max (%)', line=dict(color='#3498db', width=1, dash='dash')))
    fig_h.update_layout(title='💧 Comparaison Humidité', xaxis_title='Date', yaxis_title='%',
                        template='plotly_white', legend=dict(orientation='h', y=-0.25))
    figs_html.append(('💧 Humidité', fig_h,
        "Comparaison entre l'humidité relevée manuellement, la moyenne journalière de la station horaire et le maximum journalier."))

# Graphique 4 : THI
if 'THI' in df_csv.columns and 'Histo_THI_moy' in df_histo_jour.columns:
    df_comp2 = df_csv[['Date','THI']].merge(df_histo_jour[['Date','Histo_THI_moy','Histo_THI_max']], on='Date', how='inner')
    df_comp2 = df_comp2.dropna()
    if not df_comp2.empty:
        fig_thi = go.Figure()
        fig_thi.add_trace(go.Scatter(x=df_comp2['Date'], y=df_comp2['THI'],
                                     name='CSV THI', line=dict(color='#f39c12', width=2)))
        fig_thi.add_trace(go.Scatter(x=df_comp2['Date'], y=df_comp2['Histo_THI_moy'],
                                     name='Histo THI moy.', line=dict(color='#8e44ad', width=2, dash='dot')))
        fig_thi.add_trace(go.Scatter(x=df_comp2['Date'], y=df_comp2['Histo_THI_max'],
                                     name='Histo THI max', line=dict(color='#e74c3c', width=1, dash='dash')))
        fig_thi.update_layout(title='� Comparaison THI (Temperature-Humidity Index)',
                               xaxis_title='Date', yaxis_title='THI',
                               template='plotly_white', legend=dict(orientation='h', y=-0.25))
        figs_html.append(('🐓 THI', fig_thi,
            "Le THI (Temperature-Humidity Index) mesure le stress thermique des volailles. "
            "Seuil critique : &gt;72 = stress modéré, &gt;79 = stress sévère."))

# --- Écriture HTML ---
def couleur_mae(val, seuils=(2, 5)):
    return 'good' if val < seuils[0] else ('warn' if val < seuils[1] else 'bad')
def couleur_corr(val):
    return 'good' if val > 0.9 else ('warn' if val > 0.7 else 'bad')

with open(output_html, 'w', encoding='utf-8') as f:
    f.write('''<html><head><meta charset="utf-8"/>
<title>Vérification Cohérence Météo</title>
<style>
  body{font-family:"Segoe UI",sans-serif;background:#f4f6f9;padding:30px;color:#333;max-width:1400px;margin:0 auto}
  .header{background:linear-gradient(135deg,#2980b9,#6dd5fa);color:white;padding:30px 40px;
          border-radius:14px;margin-bottom:30px;box-shadow:0 8px 25px rgba(0,0,0,.12)}
  h1{margin:0;font-size:2rem}
  .subtitle{margin:8px 0 0;opacity:.9}
  .card{background:white;border-radius:14px;padding:25px;box-shadow:0 4px 15px rgba(0,0,0,.07);margin-bottom:28px}
  h2{color:#2c3e50;margin-top:0}
  table{border-collapse:collapse;width:100%}
  th{background:#2980b9;color:white;padding:10px 14px;text-align:left}
  td{padding:9px 14px;border-bottom:1px solid #eee}
  tr:hover{background:#f0f7ff}
  .good{color:#27ae60;font-weight:bold}
  .warn{color:#e67e22;font-weight:bold}
  .bad{color:#e74c3c;font-weight:bold}
  .note{background:#e8f4fd;border-left:4px solid #3498db;padding:12px 16px;
        border-radius:6px;margin-top:14px;font-size:.92em;color:#555}
</style></head><body>
''')
    f.write(f'''<div class="header">
  <h1>🌤️ Vérification de la Cohérence des Données Météo</h1>
  <p class="subtitle">
    <b>Source A</b> : CSV journalier (<code>df_3_meteo.csv</code>) — relevés manuels &nbsp;|&nbsp;
    <b>Source B</b> : Excel horaire (<code>Histo_Meteo.xlsx</code> → feuille <code>Histo_Meteo</code>) — station automatique
  </p>
  <p class="subtitle">Période commune : <b>{df_comp["Date"].min().date()}</b> → <b>{df_comp["Date"].max().date()}</b>
     &nbsp;|&nbsp; <b>{len(df_comp)}</b> jours analysés</p>
</div>
''')

    # Tableau métriques
    f.write('<div class="card"><h2>📋 Métriques de Cohérence</h2>')
    f.write('<table><tr><th>Comparaison</th><th>MAE</th><th>RMSE</th><th>Max écart</th><th>Corrélation</th><th>% > seuil</th><th>Nb jours</th></tr>')
    for _, r in df_resultats.iterrows():
        cm = couleur_mae(r['MAE']); cc = couleur_corr(r['Corrélation'])
        pct_val = r.get('% > seuil')
        pct_td = f"<td class='{'bad' if pct_val and pct_val > 10 else 'warn' if pct_val and pct_val > 5 else 'good'}'>{pct_val}%</td>" if pct_val is not None else "<td style='color:#ccc'>—</td>"
        f.write(f"<tr><td>{r['Comparaison']}</td>"
                f"<td class='{cm}'>{r['MAE']}</td><td>{r['RMSE']}</td>"
                f"<td>{r['Max écart']}</td><td class='{cc}'>{r['Corrélation']}</td>"
                f"{pct_td}"
                f"<td>{r['Nb jours']}</td></tr>")
    f.write('</table>')
    f.write('''<p class="note">
      <b>MAE</b> = Erreur Absolue Moyenne &nbsp;|&nbsp;
      <b>RMSE</b> = Racine Erreur Quadratique Moyenne &nbsp;|&nbsp;
      <b>% &gt; seuil</b> = % de jours dépassant le seuil d'alerte (T&gt;{seuil_t}°C) &nbsp;|&nbsp;
      <span class="good">● Bon</span> &nbsp;
      <span class="warn">● Acceptable</span> &nbsp;
      <span class="bad">● À vérifier</span>
    </p></div>''')

    # Graphiques
    for i, (titre, fig, note) in enumerate(figs_html):
        f.write(f'<div class="card"><h2>{titre}</h2>')
        f.write(fig.to_html(full_html=False, include_plotlyjs="cdn" if i == 0 else False))
        f.write(f'<p class="note">{note}</p>')
        f.write('</div>')

    # Jours aberrants
    f.write('<div class="card"><h2>⚠️ Jours avec Écarts Importants</h2>')
    f.write(f'<h3>Température – écart &gt; {seuil_t}°C : <span class="{"bad" if len(aberrants_t)>0 else "good"}">{len(aberrants_t)} jour(s)</span></h3>')
    if not aberrants_t.empty:
        f.write(aberrants_t.to_html(index=False, classes=''))
    else:
        f.write('<p class="good">✅ Aucun écart significatif</p>')

    f.write(f'<h3>Précipitations – écart &gt; {seuil_p}mm : <span class="{"bad" if len(aberrants_p)>5 else "warn" if len(aberrants_p)>0 else "good"}">{len(aberrants_p)} jour(s)</span></h3>')
    if not aberrants_p.empty:
        f.write(aberrants_p.to_html(index=False, classes=''))
    else:
        f.write('<p class="good">✅ Aucun écart significatif</p>')
    f.write('</div>')

    f.write('</body></html>')

print(f"\n✅ Rapport généré : {output_html}")
