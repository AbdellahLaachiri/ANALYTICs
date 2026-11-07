import json
import os

import pandas as pd
import yaml

from llm_analyst import generer_explication_llm

# Chargement de la configuration
with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)


def motifs_techniques(row):
    """Règles d'explicabilité : traduit les features qui s'écartent du normal en faits lisibles."""
    motifs = []
    if row.get("nb_echecs", 0) >= 3 or row.get("ratio_echecs", 0) >= 0.5:
        motifs.append(f"{int(row['nb_echecs'])} échec(s) d'authentification ou d'accès")
    if row.get("volume_max", 0) >= 100:
        motifs.append(f"Extraction massive (jusqu'à {int(row['volume_max'])} dossiers en un accès)")
    elif row.get("volume_max", 0) >= 10:
        motifs.append(f"Volume inhabituel sur un accès ({int(row['volume_max'])})")
    if row.get("nb_acces_nuit", 0) > 0:
        motifs.append(f"Activité hors horaires ({int(row['nb_acces_nuit'])} accès nocturne(s))")
    if row.get("nb_ip_externes", 0) > 0:
        motifs.append(f"Connexion depuis une IP hors réseau hôpital ({row.get('ip_suspecte')})")
    if row.get("amplitude_horaire", 0) > 14:
        motifs.append("Amplitude horaire anormale")
    return ", ".join(motifs) if motifs else "Déviation statistique comportementale globale."


def processing_moteur_alertes():
    input_csv = config["paths"]["scores"]
    output_json = config["paths"]["alerts"]
    top_n_llm = config.get("alerts", {}).get("top_n_llm", 30)

    if not os.path.exists(input_csv):
        print(f"❌ Erreur : Le fichier {input_csv} est introuvable. Lancez d'abord detection.py")
        return

    df = pd.read_csv(input_csv)
    anomalies = df[df["est_detecte"] == 1].sort_values(by="score_anomalie", ascending=False)

    print(f"➔ ANALYTIC : {len(anomalies)} alertes à qualifier "
          f"(enrichissement LLM sur les {top_n_llm} plus graves)...")

    liste_alertes = []
    for rang, (_, row) in enumerate(anomalies.iterrows(), start=1):
        score = float(row["score_anomalie"])
        explication_tech = motifs_techniques(row)

        # L'agent LLM n'enrichit que les alertes les plus graves
        explication_llm = ""
        if rang <= top_n_llm:
            explication_llm = generer_explication_llm(row["user_id"], row["severite"],
                                                      explication_tech, round(score, 4))

        liste_alertes.append({
            "id_alerte": f"ALT-{rang:04d}",
            "user_id": row["user_id"],
            "role": row["role"],
            "date_activite": str(row["date"]),
            "heure_pic": int(row["heure_pic"]),
            "ip_source": row["ip_suspecte"],
            "severite": row["severite"],
            "score_anomalie": round(score, 4),
            "explication_technique": explication_tech,
            "explication_llm": explication_llm,
            "statut": "OUVERTE",
        })

    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(liste_alertes, f, indent=4, ensure_ascii=False)

    print(f"☑ Succès : {len(liste_alertes)} alertes exportées dans {output_json}")


if __name__ == "__main__":
    processing_moteur_alertes()
