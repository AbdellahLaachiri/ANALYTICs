import requests
import json
import yaml

# Chargement de la configuration
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

def generer_explication_llm(user_id, severite, explication_technique, score):
    """Demande à l'Agent LLM d'expliquer l'anomalie de manière humaine."""
    prompt = f"""
    En tant qu'expert en cybersécurité hospitalière, explique de manière simple et non-technique cette anomalie détectée :
    - Utilisateur suspect : {user_id}
    - Gravité de l'incident : {severite}
    - Score de risque IA : {score}
    - Faits observés : {explication_technique}
    
    Donne un résumé de 2 phrases sur le danger potentiel et ajoute 2 recommandations immédiates pour l'équipe de sécurité.
    """
    
    payload = {
        "model": config["llm"]["model_name"],
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(config["llm"]["api_url"], json=payload, timeout=4)
        if response.status_code == 200:
            return response.json().get("response", "").strip()
    except Exception:
        # Mode de secours automatique (Fallback) si Ollama n'est pas lancé en local
        return (f"🚨 [ANALYSE AUTO AGENT LLM] Le profil {user_id} présente une déviation comportementale "
                f"critique basée sur les indicateurs suivants : {explication_technique}. "
                f"Recommandations : 1. Isoler temporairement la session utilisateur. "
                f"2. Déclencher un audit sur les adresses IP sources associées.")

if __name__ == "__main__":
    # Test unitaire rapide du module
    test_res = generer_explication_llm("USR_ADM_06", "CRITIQUE", "18 échecs de connexion, accès nocturnes", 0.7072)
    print("Test unitaire llm_analyst.py :\n", test_res)