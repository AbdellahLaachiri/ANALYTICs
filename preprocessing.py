"""
ANALYTIC - Prétraitement des logs (v2)

Transforme les logs bruts en features par utilisateur et par jour.
Nouveautés v2 : IP externes, ratio d'échecs, volume maximal sur un log,
heure du pic d'activité, rôle et IP principale (utilisés ensuite par les alertes
et le dashboard, à la place de données aléatoires).
"""

import pandas as pd
import yaml

with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

PREFIXE_INTERNE = config["network"]["internal_prefix"]
CLES = ["user_id", "date"]

# 1. Charger les logs
df = pd.read_csv(config["paths"]["raw_logs"])
print(f"✅ Logs chargés : {len(df)}")

# 2. Nettoyer les données
df = df.drop_duplicates()
df = df.fillna(0)
print(f"✅ Après nettoyage : {len(df)} logs")

# 3. Colonnes temporelles
df["timestamp"] = pd.to_datetime(df["timestamp"])
df["heure"] = df["timestamp"].dt.hour
df["jour_semaine"] = df["timestamp"].dt.dayofweek
df["date"] = df["timestamp"].dt.date.astype(str)

# 4. Indicateurs par log
df["est_nuit"] = ((df["heure"] >= 22) | (df["heure"] <= 5)).astype(int)
df["weekend"] = (df["jour_semaine"] >= 5).astype(int)
df["echec"] = (df["statut"] == "FAILURE").astype(int)
df["ip_externe"] = (~df["ip_source"].astype(str).str.startswith(PREFIXE_INTERNE)).astype(int)

# 5. Agrégation par utilisateur et par jour
features = df.groupby(CLES).agg(
    nb_actions=("action", "count"),
    nb_echecs=("echec", "sum"),
    volume_total=("volume", "sum"),
    volume_max=("volume", "max"),
    nb_acces_nuit=("est_nuit", "sum"),
    nb_weekend=("weekend", "sum"),
    heure_min=("heure", "min"),
    heure_max=("heure", "max"),
    nb_ip_externes=("ip_externe", "sum"),
    nb_ip_distinctes=("ip_source", "nunique"),
    role=("role", "first"),
).reset_index()

features["amplitude_horaire"] = features["heure_max"] - features["heure_min"]
features["ratio_echecs"] = (features["nb_echecs"] / features["nb_actions"]).round(4)
features = features.drop(columns=["heure_min", "heure_max"])

# 6. Contexte pour les alertes : IP suspecte (externe si présente, sinon la plus fréquente)
ip_ext = df[df["ip_externe"] == 1].groupby(CLES)["ip_source"].first().rename("ip_suspecte")
ip_main = df.groupby(CLES)["ip_source"].agg(lambda x: x.mode().iat[0]).rename("ip_principale")
ctx = pd.concat([ip_main, ip_ext], axis=1)
ctx["ip_suspecte"] = ctx["ip_suspecte"].fillna(ctx["ip_principale"])
ctx = ctx[["ip_suspecte"]].reset_index()

# Heure du log au plus gros volume de la journée
pic = df.loc[df.groupby(CLES)["volume"].idxmax(), CLES + ["heure"]].rename(columns={"heure": "heure_pic"})

features = features.merge(ctx, on=CLES, how="left").merge(pic, on=CLES, how="left")

# 7. Sauvegarde
features.to_csv(config["paths"]["features"], index=False)
print(f"✅ Features exportées → {config['paths']['features']}  ({len(features)} lignes user-jour)")
print(features.head())
