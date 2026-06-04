import pandas as pd
import json
import os

def processing_moteur_alertes():
    input_csv = "data/logs_scores.csv"
    output_json = "data/alertes.json"
    
    if not os.path.exists(input_csv):
        print(f"❌ Erreur : Le fichier {input_csv} est introuvable. Lancez d'abord detection.py")
        return

    # Lecture des données réelles issues de l'Isolation Forest d'Abdellah
    df = pd.read_csv(input_csv)
    
    liste_alertes = []
    compteur_id = 1
    
    print("➔ ANALYTIC : Analyse des scores de l'Isolation Forest et génération du contexte...")
    
    for index, row in df.iterrows():
        # On attrape uniquement les logs signalés comme anomalies par le modèle d'Abdellah
        if int(row['est_detecte']) == 1:
            score = float(row['score_anomalie'])
            severite = row['severite']
                
            # Moteur de règles contextuelles basé sur les indicateurs d'Aminata
            motifs = []
            if row.get('nb_echecs', 0) > 3:
                motifs.append(f"{int(row['nb_echecs'])} échecs de connexion (Suspicion de Brute Force)")
            if row.get('volume_total', 0) > 100:
                motifs.append(f"Volume d'accès critique ({int(row['volume_total'])} dossiers consultés)")
            if row.get('nb_acces_nuit', 0) > 0:
                motifs.append(f"{int(row['nb_acces_nuit'])} actions commises en pleine nuit")
            if row.get('amplitude_horaire', 0) > 14:
                motifs.append("Amplitude horaire de session anormalement longue")
                
            explication_finale = "Alerte comportementale : " + ", ".join(motifs) if motifs else "Déviation statistique globale détectée par l'Isolation Forest."

            # Structure de l'objet Alerte pour ton livrable JSON
            structure_alerte = {
                "id_alerte": f"ALT-{compteur_id:04d}",
                "user_id": row['user_id'],
                "date_activite": str(row['date']),
                "severite": severite,
                "score_anomalie": round(score, 4),
                "explication": explication_finale,
                "statut": "OUVERTE"
            }
            liste_alertes.append(structure_alerte)
            compteur_id += 1

    # Écriture propre du fichier JSON de sortie
    os.makedirs('data', exist_ok=True)
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(liste_alertes, f, indent=4, ensure_ascii=False)
        
    print(f"☑ Succès : {len(liste_alertes)} alertes de sécurité réelles générées dans {output_json}")

if __name__ == "__main__":
    processing_moteur_alertes()