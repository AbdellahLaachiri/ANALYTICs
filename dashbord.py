import pandas as pd
import matplotlib.pyplot as plt
import json
import os

def generer_visualisation_soc():
    json_input = "data/alertes.json"
    img_output = "data/dashboard_analytic.png"
    
    # Sécurité : Vérifier que le fichier d'alertes existe
    if not os.path.exists(json_input):
        print(f"❌ Erreur : Le fichier {json_input} est introuvable. Exécutez d'abord signalisations.py")
        return
        
    with open(json_input, 'r', encoding='utf-8') as f:
        donnees_alertes = json.load(f)
        
    df = pd.DataFrame(donnees_alertes)
    
    # Configuration graphique : Style moderne "Dark Mode"
    plt.style.use('dark_background')
    fig = plt.figure(figsize=(15, 9))
    
    # Ligne corrigée ici : Remplacement de pad=20 par y=0.98 pour éviter l'AttributeError
    fig.suptitle("ANALYTIC ── Interface de Supervision Cyber SOC Hospitalier", fontsize=18, color='#deff9a', weight='bold', y=0.98)
    
    if df.empty:
        plt.text(0.5, 0.5, "Aucune alerte active dans le système.", fontsize=14, ha='center')
        plt.savefig(img_output)
        return

    # 1. Graphique Camembert : Répartition par Sévérité
    ax1 = plt.subplot(2, 2, 1)
    comptage_sev = df['severite'].value_counts()
    code_couleurs = {'CRITIQUE': '#ff4b4b', 'ÉLEVÉ': '#ff9f1c', 'MOYEN': '#ffd166', 'FAIBLE': '#a3e635'}
    couleurs_presentes = [code_couleurs.get(x, '#deff9a') for x in comptage_sev.index]
    
    ax1.pie(comptage_sev, labels=comptage_sev.index, autopct='%1.1f%%', startangle=140, colors=couleurs_presentes,
            textprops={'fontsize': 10, 'weight': 'bold'})
    ax1.set_title("Volume d'Alertes par Niveau de Sévérité", color='#deff9a', fontsize=12, pad=10)

    # 2. Graphique Barres Horizontales : Top 5 des utilisateurs les plus suspects
    ax2 = plt.subplot(2, 2, 2)
    top_suspects = df.groupby('user_id')['score_anomalie'].max().nlargest(5).sort_values(ascending=True)
    
    barres = ax2.barh(top_suspects.index, top_suspects.values, color='#06d6a0', edgecolor='white', height=0.5)
    ax2.set_title("Top 5 des Profils Utilisateurs les plus Suspects", color='#deff9a', fontsize=12, pad=10)
    ax2.set_xlim(0, 1.0)
    
    for barre in barres:
        largeur = barre.get_width()
        ax2.text(largeur + 0.02, barre.get_y() + barre.get_height()/2, f'{largeur:.2f}', 
                 va='center', ha='left', color='white', weight='bold', fontsize=9)

    # 3. Histogramme : Distribution des scores de risque
    ax3 = plt.subplot(2, 2, 3)
    ax3.hist(df['score_anomalie'], bins=8, color='#118ab2', edgecolor='black', alpha=0.9)
    ax3.set_title("Distribution Fréquentielle des Scores d'Anomalie", color='#deff9a', fontsize=12, pad=10)
    ax3.set_xlabel("Intervalle de Score")
    ax3.set_ylabel("Nombre d'Événements")

    # 4. Table : Registre des 5 Dernières Alertes Critiques / Élevées
    ax4 = plt.subplot(2, 2, 4)
    ax4.axis('off')
    ax4.set_title("Registre des Dernières Alertes Fléchées (SOC)", color='#ff4b4b', fontsize=12, pad=10, weight='bold')
    
    alertes_prioritaires = df[df['severite'].isin(['CRITIQUE', 'ÉLEVÉ'])].head(5)
    
    position_y = 0.8
    ax4.text(0.02, 0.9, f"ID ALERTE   USER ID   SÉVÉRITÉ    SCORE     STATUT", color='#deff9a', fontsize=10, fontfamily='monospace', weight='bold')
    ax4.text(0.02, 0.85, "═" * 58, color='gray', fontsize=10)
    
    for _, ligne in alertes_prioritaires.iterrows():
        ax4.text(0.02, position_y - 0.05, f"{ligne['id_alerte']:<11} {ligne['user_id']:<9} {ligne['severite']:<11} {ligne['score_anomalie']:.4f}    {ligne['statut']}", 
                 fontsize=9.5, color='white', fontfamily='monospace')
        position_y -= 0.12

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    
    # Export automatique du livrable image pour le rapport
    plt.savefig(img_output, dpi=150)
    print(f"☑ Succès : Dashboard mis à jour visuellement et exporté dans {img_output}")
    plt.show()

if __name__ == "__main__":
    generer_visualisation_soc()