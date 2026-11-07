import requests
import yaml

# Chargement de la configuration
with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

LLM = config["llm"]


def _appeler_llm(prompt):
    """Appelle l'API Ollama locale. Renvoie le texte, ou None si l'agent est indisponible."""
    payload = {"model": LLM["model_name"], "prompt": prompt, "stream": False}
    try:
        response = requests.post(LLM["api_url"], json=payload, timeout=LLM.get("timeout", 4))
        if response.status_code == 200:
            texte = response.json().get("response", "").strip()
            return texte or None
    except Exception:
        pass
    return None


def generer_explication_llm(user_id, severite, explication_technique, score):
    """Demande à l'Agent LLM d'expliquer l'anomalie de manière humaine.
    Si Ollama n'est pas lancé (ou répond mal), renvoie une explication de secours,
    clairement signalée comme générée automatiquement sans LLM."""
    prompt = f"""
    En tant qu'expert en cybersécurité hospitalière, explique de manière simple et non-technique cette anomalie détectée :
    - Utilisateur suspect : {user_id}
    - Gravité de l'incident : {severite}
    - Score de risque IA : {score}
    - Faits observés : {explication_technique}

    Donne un résumé de 2 phrases sur le danger potentiel et ajoute 2 recommandations immédiates pour l'équipe de sécurité.
    """
    texte = _appeler_llm(prompt)
    if texte:
        return texte

    # Mode de secours (fallback) : texte gabarit, sans LLM
    return (f"[Explication automatique - LLM indisponible] Le profil {user_id} présente une anomalie "
            f"de gravité {severite} : {explication_technique}. "
            f"Recommandations : 1. Vérifier avec l'utilisateur la légitimité de ces activités. "
            f"2. Examiner les journaux d'authentification et les adresses IP associées avant toute mesure de blocage.")


def repondre_question(alerte, question):
    """Répond à une question d'investigation sur une alerte (chatbot du dashboard).
    Renvoie (texte, source) avec source = 'llm' ou 'indisponible'."""
    prompt = f"""
    Tu es un analyste SOC dans un hôpital. Contexte de l'alerte :
    - Utilisateur : {alerte.get('user_id')} (rôle : {alerte.get('role')})
    - Date : {alerte.get('date_activite')} - heure du pic : {alerte.get('heure_pic')}h - IP : {alerte.get('ip_source')}
    - Gravité : {alerte.get('severite')} - score : {alerte.get('score_anomalie')}
    - Faits observés : {alerte.get('explication_technique')}

    Question de l'analyste : {question}
    Réponds en français, de façon concise, sans inventer de faits absents du contexte.
    """
    texte = _appeler_llm(prompt)
    if texte:
        return texte, "llm"
    return ("L'agent LLM local (Ollama) n'est pas joignable : impossible de répondre à cette question pour le moment. "
            "Lancez Ollama (`ollama run llama3`) puis réessayez."), "indisponible"


if __name__ == "__main__":
    # Test unitaire rapide du module
    test_res = generer_explication_llm("USR_ADM_06", "CRITIQUE", "18 échecs de connexion, accès nocturnes", 0.7072)
    print("Test unitaire llm_analyst.py :\n", test_res)
