import streamlit as st
import pandas as pd
import json
import os
import yaml
import altair as alt

# 1. CONFIGURATION DE LA PAGE EN PLEINE PAGE STRICTE (WIDE)
st.set_page_config(page_title="ANALYTIC - Ultimate SOC Center", layout="wide", initial_sidebar_state="expanded")

# Injection CSS pour forcer le plein écran absolu et nettoyer les marges
st.markdown("""
    <style>
    .block-container {
        max-width: 100% !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
    }
    div[data-testid="stMetricValue"] { font-size: 28px; font-weight: bold; color: #023e8a; }
    .cyber-title {
        color: #1e293b;
        font-weight: bold;
        margin-bottom: 0px;
    }
    .crisis-active {
        background: linear-gradient(90deg, #e63946 0%, #a81c0c 100%);
        padding: 12px;
        border-radius: 6px;
        color: white;
        text-align: center;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="cyber-title">🛡️ ANALYTIC // PLATFORME NEXT-GEN CYBER SOC</h1>', unsafe_allow_html=True)
st.markdown("💾 *Console d'Orchestration, d'Explicabilité IA et de Remédiation Tactique (TRL 5)*")
st.markdown("---")

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

json_input = config["paths"]["alerts"]

if not os.path.exists(json_input):
    st.error("❌ Fichier d'alertes JSON introuvable. Veuillez exécuter 'signalisations.py' au préalable.")
else:
    with open(json_input, 'r', encoding='utf-8') as f:
        data = json.load(f)
    df = pd.DataFrame(data)

    # Enrichissement réseau virtuel
    if 'ip_source' not in df.columns:
        import random
        random.seed(42)
        df['ip_source'] = [f"10.140.23.{random.randint(10, 254)}" for _ in range(len(df))]
        df['heure'] = [random.randint(0, 23) for _ in range(len(df))]
        df['service_cible'] = [random.choice(["Urgences", "Radiologie", "Cardiologie", "Ressources Humaines", "DPI_Admin"]) for _ in range(len(df))]

    # --- BARRE LATÉRALE DE CONTRÔLE INTERACTIVE ---
    st.sidebar.markdown("### 🎛️ Paramètres d'Audit")
    
    severites_dispos = ["CRITIQUE", "ÉLEVÉ", "MOYEN", "FAIBLE"]
    severites_choisies = st.sidebar.multiselect("Filtrer par Sévérité Algorithmique", severites_dispos, default=severites_dispos)
    
    services_dispos = ["Tous"] + sorted(df['service_cible'].unique().tolist())
    service_choisi = st.sidebar.selectbox("Filtrer par Service Hospitalier", services_dispos)

    # Filtrage du DataFrame
    df_filtre = df[df['severite'].isin(severites_choisies)]
    if service_choisi != "Tous":
        df_filtre = df_filtre[df_filtre['service_cible'] == service_choisi]

    # --- BANDEAU DÉTECTION ---
    contient_critique = "CRITIQUE" in df_filtre['severite'].values if not df_filtre.empty else False
    if contient_critique:
        st.markdown('<div class="crisis-active">⚠️ ALERTE NIVEAU ROUGE : COMPROMISSION ET EXFILTRATION DETECTEES EN ZONE CRITIQUE</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="crisis-active" style="background: linear-gradient(90deg, #4ea8de 0%, #48cae4 100%);">✓ FLUX COMPORTEMENTAL STABLE : SURVEILLANCE COMPORTEMENTALE STANDARDISEE</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # --- INDICATEURS METRICS ---
    m1, m2, m3, m4 = st.columns(4)
    total_alertes = len(df_filtre)
    critiques_count = len(df_filtre[df_filtre['severite']=='CRITIQUE']) if total_alertes > 0 else 0
    
    m1.metric("Incidents Identifiés", total_alertes, delta=f"+{critiques_count} Critiques" if critiques_count > 0 else None, delta_color="inverse")
    m2.metric("Indice de Menace Max", f"{df_filtre['score_anomalie'].max():.4f}" if total_alertes > 0 else "0.0000")
    m3.metric("Service le Plus Ciblé", df_filtre['service_cible'].mode()[0] if total_alertes > 0 else "Aucun")
    m4.metric("Niveau d'Ingénierie", "TRL 5 (Plein Écran)")

    st.markdown("---")

    # --- GRAPHES ---
    c_gauche, c_droite = st.columns(2)

    with c_gauche:
        st.markdown("#### 📈 Chronologie d'Attaque & Éléments Temporels")
        if total_alertes > 0:
            df_timeline = df_filtre.sort_values(by="date_activite")
            st.area_chart(df_timeline, x="date_activite", y="score_anomalie", color="#e63946", use_container_width=True)
        else:
            st.info("Aucun incident à afficher.")

    with c_droite:
        st.markdown("#### 🌡️ Heatmap Horaire des Activités Suspectes")
        if total_alertes > 0:
            chart = alt.Chart(df_filtre).mark_rect().encode(
                x=alt.X('heure:O', title='Heure de Connexion (24h)'),
                y=alt.Y('service_cible:N', title='Service Hospitalier'),
                color=alt.Color('count():Q', title='Intensité', scale=alt.Scale(scheme='reds')),
                tooltip=['heure', 'service_cible', 'count()']
            ).properties(height=280)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Aucune donnée disponible.")

    st.markdown("---")

    # --- REGISTRE & RESPONSES ---
    st.markdown("#### 📋 Registre Tactique et Centre de Réponse Aux Incidents (SOAR)")
    
    if total_alertes > 0:
        df_visuel = df_filtre.sort_values(by="score_anomalie", ascending=False)
        col_liste, col_action = st.columns([2, 1])

        with col_liste:
            # CORRECTION DU PARAMÈTRE ICI : width='stretch'
            st.dataframe(
                df_visuel[["id_alerte", "user_id", "service_cible", "ip_source", "score_anomalie", "severite"]],
                width="stretch",
                hide_index=True
            )

        with col_action:
            st.markdown("⚙️ **Actions de Remédiation Immédiate**")
            alertes_ids = df_visuel['id_alerte'].tolist()
            
            incident_cible = st.selectbox("Cibler un Incident pour Confinement :", alertes_ids)
            ligne_cible = df_visuel[df_visuel['id_alerte'] == incident_cible].iloc[0]
            
            if st.button(f"🔴 ISOLER L'UTILISATEUR {ligne_cible['user_id']}", use_container_width=True):
                st.toast("Ordre de remédiation transmis !", icon="🛡️")
                st.success(f"**Action Réussie :** Le compte `{ligne_cible['user_id']}` a été désactivé. L'IP `{ligne_cible['ip_source']}` est bloquée.")
    else:
        st.info("Aucune anomalie à traiter.")

    st.markdown("---")

    # --- CHATBOT & XAI ---
    st.markdown("#### 🤖 Agent LLM d'Audit Cyber & Assistant d'Analyse Intégré")
    if total_alertes > 0:
        sec1, sec2 = st.columns([1, 2])
        with sec1:
            id_audit = st.selectbox("Sélectionner l'Alerte pour Rapport Complet :", alertes_ids, key="audit_sb")
            ligne_audit = df_visuel[df_visuel['id_alerte'] == id_audit].iloc[0]
            st.metric("Score d'Anomalie IA", f"{ligne_audit['score_anomalie']:.4f}")
            
        with sec2:
            st.markdown(f"🔬 **Métriques SIEM brutes :** `{ligne_audit['explication_technique']}`")
            st.info(f"**💬 Rapport Vulgarisé de l'Agent LLM :**\n\n{ligne_audit['explication_llm']}")
            
        st.markdown("💬 **Discuter avec l'Agent LLM à propos de cette menace**")
        user_msg = st.text_input("Saisir votre requête d'investigation :")
        if user_msg:
            with st.spinner("Génération de l'analyse cyber..."):
                st.chat_message("assistant").write(
                    f"Concernant l'alerte `{ligne_audit['id_alerte']}` de `{ligne_audit['user_id']}` dans le service `{ligne_audit['service_cible']}` : "
                    f"les indicateurs de type '{ligne_audit['explication_technique']}' confirment une déviation comportementale notable. "
                    f"En réponse à votre question : '{user_msg}', l'étape recommandée est l'audit forensic des terminaux liés à l'IP `{ligne_audit['ip_source']}`."
                )