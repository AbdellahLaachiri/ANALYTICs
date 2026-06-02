import pandas as pd

# 1. Charger les logs
df = pd.read_csv("data/logs_hospitaliers.csv")

print(f"✅ Logs chargés : {len(df)}")

# 2. Nettoyer les données
df = df.drop_duplicates()
df = df.fillna(0)

print(f"✅ Après nettoyage : {len(df)} logs")

# 3. Convertir la colonne timestamp en date
df["timestamp"] = pd.to_datetime(df["timestamp"])

# 4. Créer les colonnes temporelles
df["heure"] = df["timestamp"].dt.hour
df["jour_semaine"] = df["timestamp"].dt.dayofweek
df["date"] = df["timestamp"].dt.date

# Connexion de nuit : entre 22h et 5h
df["est_nuit"] = (
    (df["heure"] >= 22) |
    (df["heure"] <= 5)
).astype(int)

# Week-end
df["weekend"] = (
    df["jour_semaine"] >= 5
).astype(int)

# 5. Calculer l'amplitude horaire par utilisateur et par jour
amplitude = df.groupby(["user_id", "date"])["heure"].agg(
    heure_min="min",
    heure_max="max"
).reset_index()

amplitude["amplitude_horaire"] = (
    amplitude["heure_max"] - amplitude["heure_min"]
)

# 6. Créer les features finales
features = df.groupby(["user_id", "date"]).agg(
    nb_actions=("action", "count"),
    nb_echecs=("statut", lambda x: (x == "FAILURE").sum()),
    volume_total=("volume", "sum"),
    nb_acces_nuit=("est_nuit", "sum"),
    nb_weekend=("weekend", "sum")
).reset_index()

# 7. Ajouter amplitude_horaire
features = features.merge(
    amplitude[["user_id", "date", "amplitude_horaire"]],
    on=["user_id", "date"],
    how="left"
)

# 8. Sauvegarder le fichier final
features.to_csv("data/logs_features.csv", index=False)

print("✅ Features exportées → data/logs_features.csv")
print(features.head())