"""
ANALYTIC - Détection d'anomalies par Isolation Forest (v2)
Auteur : Abdellah L.

v2 : paramètres lus dans config.yaml, features enrichies (IP externes, ratio d'échecs,
volume max, ...), sévérité calculée sur la distribution des scores des anomalies détectées.
"""

import pandas as pd
import yaml
from sklearn.ensemble import IsolationForest


def charger_config(chemin="config.yaml"):
    with open(chemin, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def calculer_scores(df, features, contamination, n_estimators=200, random_state=42):
    """Entraîne un Isolation Forest et renvoie df + score_anomalie / prediction / est_detecte."""
    X = df[features].fillna(0)
    model = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        random_state=random_state,
        n_jobs=-1,
    )
    model.fit(X)
    out = df.copy()
    out["prediction_raw"] = model.predict(X)
    out["score_anomalie"] = -model.score_samples(X)
    out["est_detecte"] = (out["prediction_raw"] == -1).astype(int)
    return out


def attribuer_severite(df):
    """Sévérité relative aux anomalies détectées : top 10 % = CRITIQUE, 10-40 % = ÉLEVÉ, reste = MOYEN.
    Les journées non détectées sont FAIBLE."""
    sev = pd.Series("FAIBLE", index=df.index)
    det = df["est_detecte"] == 1
    if det.any():
        q60 = df.loc[det, "score_anomalie"].quantile(0.60)
        q90 = df.loc[det, "score_anomalie"].quantile(0.90)
        sev[det] = "MOYEN"
        sev[det & (df["score_anomalie"] >= q60)] = "ÉLEVÉ"
        sev[det & (df["score_anomalie"] >= q90)] = "CRITIQUE"
    return sev


def main():
    config = charger_config()
    df = pd.read_csv(config["paths"]["features"])
    print(f"✅ {len(df)} entrées chargées")

    m = config["model"]
    df = calculer_scores(df, m["features"], m["contamination"], m["n_estimators"], m["random_state"])
    df["severite"] = attribuer_severite(df)
    print("✅ Modèle entraîné")

    total = len(df)
    detectes = int(df["est_detecte"].sum())
    print("\n📊 Résultats de la détection :")
    print(f"   Total analysé         : {total}")
    print(f"   Comportements normaux : {total - detectes}")
    print(f"   Anomalies détectées   : {detectes}")
    print(f"   Taux d'anomalies      : {detectes / total * 100:.1f}%")

    print("\n📊 Répartition par sévérité :")
    for niveau in ["CRITIQUE", "ÉLEVÉ", "MOYEN", "FAIBLE"]:
        print(f"   {niveau:10s} : {(df['severite'] == niveau).sum()}")

    df.to_csv(config["paths"]["scores"], index=False)
    print(f"\n✅ Résultats exportés → {config['paths']['scores']}")


if __name__ == "__main__":
    main()
