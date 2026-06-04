import pandas as pd
import json
import os

def processing_moteur_alertes():
    input_csv = "data/logs_scores.csv"
    output_json = "data/alertes.json"
    
    if not os.path.exists(input_csv):
        print(f"❌ Erreur : Le fichier {input_csv} est introuvable. Lancez d'abord detection.py")
        return

    # Connexion directe aux résultats réels de l'Isolation Forest
    df = pd.read_csv(input_csv)
    
    liste_alertes = []
    compteur_id = 1
    
    print("➔ ANALYTIC : Analyse contextuelle des logs signalés par l'Isolation Forest...")
    
    for index, row in df.iterrows():
        # Filtrage strict : on ne prend que les lignes qualifiées d'anomalies par l'IA
        if int(row['est_detecte']) == 1:
            score = float(row['score_anomalie'])
            severite = row['severite']
                
            # Moteur d'explicabilité cyber basé sur les indicateurs d'Aminata
            motifs = []
            if row.get('nb_echecs', 0) > 3:
                motifs.append(f"{int(row['nb_echecs'])} échecs d'authentification (Brute Force suspecté)")
            if row.get('volume_total', 0) > 100:
                motifs.append(f"Extraction massive de données ({int(row['volume_total'])} fichiers patients consultés)")
            if row.get('nb_acces_nuit', 0) > 0:
                motifs.append(f"Activité hors horaires standards ({int(row['nb_acces_nuit'])} accès nocturnes)")
            if row.get('amplitude_horaire', 0) > 14:
                motifs.append(f"Session anormalement prolongée ({int(row['amplitude_horaire'])}h d'activité)")
                
            explication_finale = "Alerte SIEM ➔ " + ", ".join(motifs) if motifs else "Déviation statistique comportementale majeure (Isolation Forest)."

            # Modélisation de l'incident au format normalisé SOC
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

    # Persistance des données en JSON propre
    os.makedirs('data', exist_ok=True)
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(liste_alertes, f, indent=4, ensure_ascii=False)
        
    print(f"☑ Succès : {len(liste_alertes)} alertes réelles qualifiées exportées dans {output_json}")

if __name__ == "__main__":
    processing_moteur_alertes()