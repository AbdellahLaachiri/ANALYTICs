"""
ANALYTIC - Évaluation de la détection contre la vérité terrain (colonne est_anomalie du générateur).

Compare trois approches au niveau user-jour :
  - Isolation Forest v1 (les 6 features d'origine)
  - Isolation Forest v2 (features de config.yaml)
  - Baseline à règles (seuils fixes, façon SIEM classique)

Métriques : précision, rappel, F1 au seuil d'alerte, plus des métriques indépendantes du seuil
(ROC-AUC, précision@k). Le rappel par scénario est calculé au niveau des logs anormaux.

Lancer après preprocessing.py :  python evaluation.py
"""

import json

import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

from detection import calculer_scores, charger_config

FEATURES_V1 = ["nb_actions", "nb_echecs", "volume_total", "nb_acces_nuit",
               "nb_weekend", "amplitude_horaire"]


def prf(vrai, pred):
    tp = int(((vrai == 1) & (pred == 1)).sum())
    fp = int(((vrai == 0) & (pred == 1)).sum())
    fn = int(((vrai == 1) & (pred == 0)).sum())
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": round(p, 3),
            "rappel": round(r, 3), "f1": round(f1, 3)}


def precision_at_k(vrai, score, k):
    top = vrai.loc[score.sort_values(ascending=False).index[:k]]
    return round(float(top.mean()), 3)


def scenario(row):
    """Le CSV ne contient que est_anomalie : on retrouve le scénario d'après ses signatures."""
    if not str(row["ip_source"]).startswith("192.168."):
        return "ip_inconnue"
    if row["volume"] >= 200:
        return "massif"
    if row["action"] == "ACCES_SYSTEME" and row["statut"] == "FAILURE" and row["volume"] >= 10:
        return "brute_force"
    return "nuit"


def main():
    cfg = charger_config()
    feats = pd.read_csv(cfg["paths"]["features"])
    feats["date"] = feats["date"].astype(str)

    logs = pd.read_csv(cfg["paths"]["raw_logs"]).drop_duplicates()
    logs["timestamp"] = pd.to_datetime(logs["timestamp"])
    logs["date"] = logs["timestamp"].dt.date.astype(str)

    vrai = logs.groupby(["user_id", "date"])["est_anomalie"].max().rename("vrai").reset_index()
    df = feats.merge(vrai, on=["user_id", "date"], how="left")
    df["vrai"] = df["vrai"].fillna(0).astype(int)

    m = cfg["model"]
    cont = m["contamination"]
    n_pos = int(df["vrai"].sum())
    print(f"User-jours : {len(df)} dont {n_pos} avec une vraie attaque ({n_pos / len(df):.1%})")
    print(f"Seuil d'alerte (contamination) : {cont:.0%} des journées\n")

    resultats = {"n_user_jours": len(df), "n_vrais_anormaux": n_pos, "contamination": cont}
    k = int(round(cont * len(df)))

    # --- Isolation Forest v1 et v2 ---
    run = {}
    for nom, f in [("IF_v1_6_features", FEATURES_V1), ("IF_v2", m["features"])]:
        r = calculer_scores(df, f, cont, m["n_estimators"], m["random_state"])
        run[nom] = r
        res = prf(r["vrai"], r["est_detecte"])
        res["roc_auc"] = round(roc_auc_score(r["vrai"], r["score_anomalie"]), 3)
        res["avg_precision"] = round(average_precision_score(r["vrai"], r["score_anomalie"]), 3)
        res[f"precision@{k}"] = precision_at_k(r["vrai"], r["score_anomalie"], k)
        resultats[nom] = res

    # --- Baseline à règles ---
    regle = ((df["nb_echecs"] >= 3) | (df["volume_max"] >= 10) |
             (df["nb_ip_externes"] > 0) | (df["nb_acces_nuit"] > 0)).astype(int)
    resultats["regles_seuils_fixes"] = prf(df["vrai"], regle)

    # --- Sensibilité au seuil d'alerte (IF v2) ---
    sweep = {}
    for c in [0.05, 0.10, 0.20, 0.30, round(n_pos / len(df), 2)]:
        r = calculer_scores(df, m["features"], c, m["n_estimators"], m["random_state"])
        sweep[str(c)] = prf(r["vrai"], r["est_detecte"])
    resultats["IF_v2_selon_contamination"] = sweep

    # --- Rappel par scénario (niveau log) ---
    a = logs[logs["est_anomalie"] == 1].copy()
    a["scenario"] = a.apply(scenario, axis=1)
    a = a.merge(run["IF_v1_6_features"][["user_id", "date", "est_detecte"]].rename(
        columns={"est_detecte": "v1"}), on=["user_id", "date"], how="left")
    a = a.merge(run["IF_v2"][["user_id", "date", "est_detecte"]].rename(
        columns={"est_detecte": "v2"}), on=["user_id", "date"], how="left")
    a = a.merge(df[["user_id", "date"]].assign(regles=regle.values), on=["user_id", "date"], how="left")
    par_scen = a.groupby("scenario")[["v1", "v2", "regles"]].mean().round(3)
    par_scen.insert(0, "nb_logs", a.groupby("scenario").size())
    resultats["rappel_par_scenario"] = par_scen.to_dict(orient="index")

    # --- Affichage ---
    print("=== Au seuil d'alerte ===")
    tab = pd.DataFrame({n: resultats[n] for n in ["IF_v1_6_features", "IF_v2", "regles_seuils_fixes"]}).T
    print(tab.to_string())
    print("\n=== IF v2 selon le seuil d'alerte (contamination) ===")
    print(pd.DataFrame(sweep).T[["precision", "rappel", "f1"]].to_string())
    print("\n=== Rappel par scénario (part des logs anormaux couverts par une alerte) ===")
    print(par_scen.to_string())

    with open(cfg["paths"]["evaluation"], "w", encoding="utf-8") as f:
        json.dump(resultats, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Résultats exportés → {cfg['paths']['evaluation']}")


if __name__ == "__main__":
    main()
