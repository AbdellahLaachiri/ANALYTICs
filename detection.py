"""
ANALYTIC - Détection d'anomalies par Isolation Forest
Auteur : Abdellah L.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

FICHIER_ENTREE = "data/logs_features.csv"
FICHIER_SORTIE = "data/logs_scores.csv"

# Chargement des données
df = pd.read_csv(FICHIER_ENTREE)
print(f"✅ {len(df)} entrées chargées")

# Features utilisées pour la détection
FEATURES = [
    "nb_actions",
    "nb_echecs",
    "volume_total",
    "nb_acces_nuit",
    "nb_weekend",
    "amplitude_horaire",
]

X = df[FEATURES].fillna(0)

# Entraînement du modèle
model = IsolationForest(
    n_estimators=200,
    contamination=0.10,
    random_state=42,
    n_jobs=-1
)
model.fit(X)
print("✅ Modèle entraîné")

# Prédiction
df["prediction_raw"] = model.predict(X)
df["score_anomalie"] = -model.score_samples(X)
df["est_detecte"]    = (df["prediction_raw"] == -1).astype(int)

# Niveau de sévérité
def attribuer_severite(score):
    if score > 0.7:
        return "CRITIQUE"
    elif score > 0.55:
        return "ÉLEVÉ"
    elif score > 0.45:
        return "MOYEN"
    else:
        return "FAIBLE"

df["severite"] = df["score_anomalie"].apply(attribuer_severite)

# Résultats
total     = len(df)
detectes  = int(df["est_detecte"].sum())
normaux   = total - detectes

print(f"\n📊 Résultats de la détection :")
print(f"   Total analysé       : {total}")
print(f"   Comportements normaux : {normaux}")
print(f"   Anomalies détectées   : {detectes}")
print(f"   Taux d'anomalies      : {detectes/total*100:.1f}%")

print(f"\n📊 Répartition par sévérité :")
for niveau in ["CRITIQUE", "ÉLEVÉ", "MOYEN", "FAIBLE"]:
    count = (df["severite"] == niveau).sum()
    print(f"   {niveau:10s} : {count}")

# Export
df.to_csv(FICHIER_SORTIE, index=False)
print(f"\n✅ Résultats exportés → {FICHIER_SORTIE}")