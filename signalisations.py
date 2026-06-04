import pandas as pd
import json
import os
import yaml
from llm_analyst import generer_explication_llm

# Chargement de la configuration
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

def processing_moteur_alertes():
    input_csv = config["paths"]["scores"]
    output_json = config["paths"]["alerts"]
    
    if not os.path.exists(input_csv):
        print(f"❌ Erreur : Le fichier {input_csv} est introuvable. Lancez d'abord detection.py")
        return

    # Lecture des données réelles issues de l'Isolation Forest
    df = pd.read_csv(input_csv)
    liste_alertes = []
    compteur_id = 1
    
    print("➔ ANALYTIC : Qualification des incidents et enrichissement par l'Agent LLM...")
    
    # Filtrage et tri des anomalies pour traiter le Top 10 des pires menaces de manière fluide
    anomalies = df[df['est_detecte'] == 1].sort_values(by="score_anomalie", ascending=False).head(10)
    
    for index, row in anomalies.iterrows():
        score = float(row['score_anomalie'])
        severite = row['severite']
        user_id = row['user_id']
            
        # Règles d'explicabilité contextuelle basées sur les indicateurs d'Aminata
        motifs = []
        if row.get('nb_echecs', 0) > 3:
            motifs.append(f"{int(row['nb_echecs'])} échecs d'authentification")
        if row.get('volume_total', 0) > 100:
            motifs.append(f"Extraction massive ({int(row['volume_total'])} fichiers patients)")
        if row.get('nb_acces_nuit', 0) > 0:
            motifs.append(f"Activité hors horaires ({int(row['nb_acces_nuit'])} accès nocturnes)")
        if row.get('amplitude_horaire', 0) > 14:
            motifs.append("Amplitude horaire anormale")
            
        explication_tech = ", ".join(motifs) if motifs else "Déviation statistique comportementale globale."
        
        # Enrichissement via l'Agent LLM
        explication_naturelle = generer_explication_llm(user_id, severite, explication_tech, round(score, 4))

        structure_alerte = {
            "id_alerte": f"ALT-{compteur_id:04d}",
            "user_id": user_id,
            "date_activite": str(row['date']),
            "severite": severite,
            "score_anomalie": round(score, 4),
            "explication_technique": explication_tech,
            "explication_llm": explication_naturelle,
            "statut": "OUVERTE"
        }
        liste_alertes.append(structure_alerte)
        compteur_id += 1

    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(liste_alertes, f, indent=4, ensure_ascii=False)
        
    print(f"☑ Succès : {len(liste_alertes)} incidents enrichis exportés dans {output_json}")

if __name__ == "__main__":
    processing_moteur_alertes()