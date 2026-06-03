import csv
import random
from datetime import datetime, timedelta
import os

# Configuration globale
NUM_LOGS = 10000
NUM_ANOMALIES = 1000
NUM_NORMALS = NUM_LOGS - NUM_ANOMALIES

# Base de simulation (Utilisateurs et adresses IP de l'hôpital)
USERS = {
    'medecin': [f'USR_MED_{i:02d}' for i in range(1, 21)],      # 20 médecins
    'infirmier': [f'USR_INF_{i:02d}' for i in range(1, 21)],    # 20 infirmiers
    'admin': [f'USR_ADM_{i:02d}' for i in range(1, 11)]         # 10 admins
}
IPS_CONNUES = [f'192.168.1.{i}' for i in range(10, 100)]

# Génération d'une date aléatoire sur la période du projet (45 jours en 2026)
START_DATE = datetime(2026, 4, 15)

def get_random_timestamp(role):
    """Génère une heure de connexion réaliste selon le rôle"""
    days_offset = random.randint(0, 44)
    date_base = START_DATE + timedelta(days=days_offset)
    
    if role == 'medecin':
        hour = random.randint(8, 19) # 8h - 20h
    elif role == 'infirmier':
        hour = random.randint(6, 21) # 6h - 22h
    else: # admin
        hour = random.randint(8, 17) # 8h - 18h
        
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return date_base.replace(hour=hour, minute=minute, second=second)

def generate_normal_log():
    """Génère un seul log au comportement totalement normal"""
    role = random.choice(['medecin', 'infirmier', 'admin'])
    user_id = random.choice(USERS[role])
    timestamp = get_random_timestamp(role)
    ip_source = random.choice(IPS_CONNUES)
    
    # Comportement spécifique selon le métier
    if role == 'medecin':
        action = random.choice(['ACCES_DPI', 'CONSULTATION', 'PRESCRIPTION'])
        volume = random.randint(1, 5) # Quelques dossiers à la fois
    elif role == 'infirmier':
        action = random.choice(['ACCES_DPI', 'PRISE_EN_CHARGE'])
        volume = random.randint(1, 3)
    else: # admin
        action = random.choice(['ACCES_SYSTEME', 'CONFIGURATION'])
        volume = 0 # Pas de dossiers médicaux pour la technique
        
    # Un log normal est presque toujours un succès
    statut = 'SUCCESS' if random.random() > 0.02 else 'FAILURE' 
    
    return {
        'user_id': user_id,
        'role': role,
        'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'action': action,
        'ip_source': ip_source,
        'statut': statut,
        'volume': volume,
        'est_anomalie': 0
    }

def generate_anomaly_log(start_date):
    """Génère un log anormal basé sur l'un des 4 scénarios d'attaque."""
    # Choisir un scénario au hasard parmi les 4 définis dans le guide
    scenario = random.choice(['nuit', 'massif', 'ip_inconnue', 'brute_force'])
    
    # On choisit un utilisateur et son rôle au hasard pour l'attaque
    role = random.choice(['medecin', 'infirmier', 'admin'])
    user_id = random.choice(USERS[role])
    
    # Par défaut, on reprend des valeurs normales qu'on va modifier selon le scénario
    ip = random.choice(IPS_CONNUES)
    action = random.choice(['ACCES_DPI', 'CONSULTATION'])
    statut = 'SUCCESS'
    volume = random.randint(1, 3)
    
    # Configuration des dates sur les 45 jours
    days_offset = random.randint(0, 44)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)

    # --- SCÉNARIO 1 : Connexion de nuit (Entre 1h et 4h du matin) ---
    if scenario == 'nuit':
        hour = random.randint(1, 3)
        volume = random.randint(1, 5)

    # --- SCÉNARIO 2 : Accès massif (Gros volume de dossiers d'un coup) ---
    elif scenario == 'massif':
        hour = random.randint(8, 18) # Heure normale pour essayer de se fondre dans la masse
        volume = random.randint(200, 500) # Volume anormal d'accès massifs

    # --- SCÉNARIO 3 : IP inconnue (Connexion hors réseau hôpital) ---
    elif scenario == 'ip_inconnue':
        hour = random.randint(8, 18)
        # Génère une IP externe suspecte (ex: 45.x.x.x) au lieu de 192.168.x.x
        ip = f"45.{random.randint(10, 250)}.{random.randint(10, 250)}.{random.randint(10, 250)}"

    # --- SCÉNARIO 4 : Brute force (Tentatives d'authentification en échec) ---
    elif scenario == 'brute_force':
        hour = random.randint(8, 18)
        action = 'ACCES_SYSTEME'
        statut = 'FAILURE' # Indispensable pour marquer l'échec
        volume = random.randint(10, 30) # Trop d'échecs d'un coup

    # Calcul du timestamp final
    log_date = start_date + timedelta(days=days_offset, hours=hour, minutes=minute, seconds=second)

    return {
        'user_id': user_id,
        'role': role,
        'timestamp': log_date.strftime('%Y-%m-%d %H:%M:%S'),
        'action': action,
        'ip_source': ip,
        'statut': statut,
        'volume': volume,
        'est_anomalie': 1 
    }

if __name__ == "__main__":
    # Date de début de la simulation (il y a 45 jours par rapport à début juin 2026)
    START_DATE = datetime(2026, 4, 15)
    
    print("Generation des logs hospitaliers en cours...")
    
    logs = []
    
    # 1. Génération des 9 000 logs normaux
    for _ in range(NUM_NORMALS):
        logs.append(generate_normal_log())
        
    # 2. Génération des 1 000 logs d'anomalies
    for _ in range(NUM_ANOMALIES):
        logs.append(generate_anomaly_log(START_DATE))
        
    # 3. Mélanger les logs de manière aléatoire
    random.shuffle(logs)
    
    # 4. S'assurer que le dossier 'data' existe
    os.makedirs('data', exist_ok=True)
    
    # 5. Écriture du fichier CSV
    csv_fields = ['user_id', 'role', 'timestamp', 'action', 'ip_source', 'statut', 'volume', 'est_anomalie']
    csv_file_path = "data/logs_hospitaliers.csv"
    
    try:
        with open(csv_file_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=csv_fields)
            writer.writeheader()
            writer.writerows(logs)
            
        print(f"Succes : {NUM_LOGS} logs generes -> {csv_file_path}")
        print(f"   - Normaux   : {NUM_NORMALS}")
        print(f"   - Anomalies : {NUM_ANOMALIES}")
        
    except Exception as e:
        print(f"Erreur lors de l'ecriture du fichier : {e}")