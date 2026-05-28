"""
frontend/app.py — Interface Streamlit pour le système médical multi-agents
4 écrans : saisie → questions → revue médecin → rapport final
"""
import streamlit as st
import requests
import time
from fpdf import FPDF

def generate_report_pdf(s) -> bytes:
    pdf = FPDF()
    pdf.add_page()

    # ── Police Unicode (Arial système Windows) ─────────────────────
    # ❌ AVANT : pdf.set_font("Helvetica", ...) → Latin-1, plante sur œ é à ç
    # ✅ APRÈS : Arial TTF → Unicode complet, support français garanti
    pdf.add_font("Arial", style="",  fname=r"C:\Windows\Fonts\arial.ttf")
    pdf.add_font("Arial", style="B", fname=r"C:\Windows\Fonts\arialbd.ttf")
    pdf.add_font("Arial", style="I", fname=r"C:\Windows\Fonts\ariali.ttf")
    pdf.add_font("Arial", style="BI", fname=r"C:\Windows\Fonts\arialbi.ttf")
    # ───────────────────────────────────────────────────────────────

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "RAPPORT DE CONSULTATION MEDICALE", ln=True, align="C")
    pdf.set_font("Arial", "I", 9)
    pdf.cell(0, 6, "Usage academique uniquement", ln=True, align="C")
    pdf.ln(5)

    def section(title, content):
        pdf.set_font("Arial", "B", 11)        # ← Arial partout
        pdf.set_fill_color(30, 80, 160)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 8, title, ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "", 10)          # ← Arial partout
        pdf.multi_cell(0, 6, content or "Non disponible")
        pdf.ln(3)

    section("PATIENT", f"{s.patient_name} - {s.initial_complaint}")
    qa_text = "\n".join(
        f"Q{i}: {q}\n-> {a}" for i, (q, a) in enumerate(s.qa_history, 1)
    )
    section("ENTRETIEN PATIENT", qa_text)
    section("SYNTHESE DIAGNOSTIQUE (IA)", s.diagnostic_summary)
    section("RECOMMANDATIONS MCP", s.interim_care)
    section("OBSERVATIONS MEDECIN", s.physician_review)
    section("PLAN DE TRAITEMENT", s.treatment_plan)

    return bytes(pdf.output())

# ── Config ─────────────────────────────────────────────────────────────────────
API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Assistant Médical",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── CSS custom ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', sans-serif;
    }

    .main { background-color: #0f1117; }

    .stApp {
        background: linear-gradient(135deg, #0f1117 0%, #1a1f2e 100%);
        min-height: 100vh;
    }

    /* Header */
    .med-header {
        text-align: center;
        padding: 2rem 0 1rem 0;
        border-bottom: 1px solid #2d3748;
        margin-bottom: 2rem;
    }
    .med-header h1 {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1.8rem;
        color: #63b3ed;
        letter-spacing: 0.1em;
        margin: 0;
    }
    .med-header p {
        color: #718096;
        font-size: 0.85rem;
        margin: 0.3rem 0 0 0;
        font-family: 'IBM Plex Mono', monospace;
    }

    /* Step indicator */
    .step-bar {
        display: flex;
        justify-content: center;
        gap: 0.5rem;
        margin-bottom: 2.5rem;
        padding: 0 1rem;
    }
    .step {
        flex: 1;
        max-width: 160px;
        text-align: center;
        font-size: 0.7rem;
        font-family: 'IBM Plex Mono', monospace;
        padding: 0.4rem 0.5rem;
        border-radius: 4px;
        border: 1px solid #2d3748;
        color: #4a5568;
        background: #1a202c;
        transition: all 0.3s;
    }
    .step.active {
        border-color: #63b3ed;
        color: #63b3ed;
        background: #1a2535;
        font-weight: 600;
    }
    .step.done {
        border-color: #48bb78;
        color: #48bb78;
        background: #1a2520;
    }

    /* Cards */
    .med-card {
        background: #1a202c;
        border: 1px solid #2d3748;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .med-card h3 {
        color: #63b3ed;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.85rem;
        letter-spacing: 0.08em;
        margin: 0 0 1rem 0;
        text-transform: uppercase;
    }

    /* Question bubble */
    .question-bubble {
        background: #1a2535;
        border-left: 3px solid #63b3ed;
        border-radius: 0 8px 8px 0;
        padding: 1rem 1.2rem;
        margin-bottom: 1.5rem;
        font-size: 1.05rem;
        color: #e2e8f0;
        line-height: 1.6;
    }

    /* Answer history */
    .qa-item {
        margin-bottom: 0.8rem;
        padding: 0.6rem 0.8rem;
        background: #0f1117;
        border-radius: 6px;
        border: 1px solid #2d3748;
    }
    .qa-q { color: #63b3ed; font-size: 0.8rem; font-family: 'IBM Plex Mono', monospace; }
    .qa-a { color: #a0aec0; font-size: 0.9rem; margin-top: 0.2rem; }

    /* Progress */
    .progress-label {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.75rem;
        color: #718096;
        text-align: right;
        margin-bottom: 0.3rem;
    }

    /* Severity badge */
    .severity-low    { color: #48bb78; font-weight: 600; }
    .severity-medium { color: #ed8936; font-weight: 600; }
    .severity-high   { color: #fc8181; font-weight: 600; }

    /* Report sections */
    .report-section {
        background: #0f1117;
        border: 1px solid #2d3748;
        border-radius: 6px;
        padding: 1rem;
        margin-bottom: 0.8rem;
    }
    .report-section h4 {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.75rem;
        color: #718096;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin: 0 0 0.5rem 0;
    }
    .report-section p {
        color: #e2e8f0;
        font-size: 0.95rem;
        margin: 0;
        line-height: 1.6;
        white-space: pre-wrap;
    }

    /* Buttons override */
    .stButton > button {
        background: #2b6cb0;
        color: white;
        border: none;
        border-radius: 6px;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.85rem;
        letter-spacing: 0.05em;
        padding: 0.6rem 1.5rem;
        transition: background 0.2s;
    }
    .stButton > button:hover {
        background: #3182ce;
        border: none;
    }

    /* Input override */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: #0f1117;
        border: 1px solid #2d3748;
        color: #e2e8f0;
        border-radius: 6px;
        font-family: 'IBM Plex Sans', sans-serif;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #63b3ed;
        box-shadow: 0 0 0 1px #63b3ed;
    }

    /* Alert */
    .alert-warning {
        background: #2d2008;
        border: 1px solid #d69e2e;
        border-radius: 6px;
        padding: 0.8rem 1rem;
        color: #f6e05e;
        font-size: 0.85rem;
        margin-bottom: 1rem;
    }
    .alert-success {
        background: #0d2016;
        border: 1px solid #48bb78;
        border-radius: 6px;
        padding: 0.8rem 1rem;
        color: #68d391;
        font-size: 0.85rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# ── State management ───────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "screen": 1,                 # 1=saisie, 2=questions, 3=médecin, 4=rapport
        "session_id": None,
        "thread_id": None,
        "patient_name": "",
        "initial_complaint": "",
        "current_question": None,
        "question_index": 0,
        "total_questions": 5,
        "qa_history": [],            # [(question, réponse), ...]
        "diagnostic_summary": None,
        "interim_care": None,
        "physician_review": None,
        "treatment_plan": None,
        "final_report": None,
        "error": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()
s = st.session_state


# ── API helpers ────────────────────────────────────────────────────────────────
def api_post(path: str, data: dict) -> dict | None:
    try:
        r = requests.post(f"{API_URL}{path}", json=data, timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        s.error = "❌ API non disponible — lancez : uvicorn backend.app.api:app --port 8000"
        return None
    except Exception as e:
        s.error = f"❌ Erreur API : {e}"
        return None

def api_get(path: str) -> dict | None:
    try:
        r = requests.get(f"{API_URL}{path}", timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        s.error = f"❌ Erreur API : {e}"
        return None


# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="med-header">
    <h1>🏥 ASSISTANT MÉDICAL</h1>
    <p>Système d'orientation clinique préliminaire · Usage académique uniquement</p>
</div>
""", unsafe_allow_html=True)


# ── Step bar ───────────────────────────────────────────────────────────────────
steps = ["01 · Saisie", "02 · Questions", "03 · Médecin", "04 · Rapport"]
step_html = '<div class="step-bar">'
for i, label in enumerate(steps, 1):
    cls = "active" if s.screen == i else ("done" if s.screen > i else "step")
    step_html += f'<div class="step {cls}">{label}</div>'
step_html += '</div>'
st.markdown(step_html, unsafe_allow_html=True)


# ── Error banner ───────────────────────────────────────────────────────────────
if s.error:
    st.markdown(f'<div class="alert-warning">{s.error}</div>', unsafe_allow_html=True)
    s.error = None


# ══════════════════════════════════════════════════════════════════════════════
# ÉCRAN 1 — Saisie du cas patient
# ══════════════════════════════════════════════════════════════════════════════
if s.screen == 1:
    st.markdown('<div class="med-card"><h3>📋 Informations patient</h3>', unsafe_allow_html=True)

    patient_name = st.text_input(
        "Nom du patient",
        value=s.patient_name,
        placeholder="ex : Jean Dupont",
    )
    initial_complaint = st.text_area(
        "Motif de consultation",
        value=s.initial_complaint,
        placeholder="Décrivez brièvement vos symptômes principaux...",
        height=120,
    )

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="alert-warning">⚠️ Ce système est un outil académique. Il ne remplace pas une consultation médicale réelle.</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col2:
        start_btn = st.button("Démarrer →", use_container_width=True)

    if start_btn:
        if not patient_name.strip() or not initial_complaint.strip():
            st.warning("Veuillez renseigner le nom et le motif de consultation.")
        else:
            s.patient_name = patient_name
            s.initial_complaint = initial_complaint

            with st.spinner("Création de la session..."):
                # 1. Créer session
                session_res = api_post("/start_session", {
                    "patient_name": patient_name,
                    "metadata": {}
                })
                if not session_res:
                    st.stop()

                s.session_id = session_res["session_id"]

                # 2. Démarrer consultation
                consult_res = api_post("/start_consultation", {
                    "session_id": s.session_id,
                    "initial_complaint": initial_complaint,
                })
                if not consult_res:
                    st.stop()

                s.thread_id        = consult_res["thread_id"]
                s.current_question = consult_res.get("question")
                s.question_index   = consult_res.get("question_index", 0)
                s.total_questions  = consult_res.get("total_questions", 5)
                s.screen = 2
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# ÉCRAN 2 — Questions / Réponses patient
# ══════════════════════════════════════════════════════════════════════════════
elif s.screen == 2:
    # Progress
    progress = (s.question_index) / s.total_questions
    st.markdown(f'<div class="progress-label">Question {s.question_index + 1} / {s.total_questions}</div>', unsafe_allow_html=True)
    st.progress(progress)

    # Question courante
    if s.current_question:
        st.markdown(f'<div class="question-bubble">🩺 {s.current_question}</div>', unsafe_allow_html=True)

        answer = st.text_area(
            "Votre réponse",
            key=f"answer_{s.question_index}",
            placeholder="Décrivez en détail...",
            height=100,
            label_visibility="collapsed",
        )

        col1, col2 = st.columns([3, 1])
        with col2:
            next_btn = st.button("Suivant →", use_container_width=True)

        if next_btn:
            if not answer.strip():
                st.warning("Veuillez répondre à la question avant de continuer.")
            else:
                # Sauvegarde dans l'historique
                s.qa_history.append((s.current_question, answer))

                with st.spinner("Traitement..."):
                    resume_res = api_post("/consultation/resume", {
                        "thread_id": s.thread_id,
                        "patient_answer": answer,
                    })

                if not resume_res:
                    st.stop()

                status = resume_res.get("status")

                if status == "pending_answer":
                    # Prochaine question
                    s.current_question = resume_res.get("question")
                    s.question_index   = resume_res.get("question_index", s.question_index + 1)
                    st.rerun()

                elif status in ("physician_review", "completed"):
                    # Récupère l'état complet
                    state = api_get(f"/consultation/{s.thread_id}")
                    if state:
                        s.diagnostic_summary = state.get("diagnostic_summary")
                        s.interim_care       = state.get("interim_care")
                    s.screen = 3
                    st.rerun()

    # Historique Q/R
    if s.qa_history:
        st.markdown("---")
        st.markdown('<div class="med-card"><h3>📝 Réponses précédentes</h3>', unsafe_allow_html=True)
        for q, a in s.qa_history:
            st.markdown(f"""
            <div class="qa-item">
                <div class="qa-q">Q — {q}</div>
                <div class="qa-a">↳ {a}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# ÉCRAN 3 — Revue médecin
# ══════════════════════════════════════════════════════════════════════════════
elif s.screen == 3:
    st.markdown('<div class="med-card"><h3>🔬 Synthèse diagnostique (IA)</h3>', unsafe_allow_html=True)

    if s.diagnostic_summary:
        st.markdown(f"""
        <div class="report-section">
            <h4>Synthèse clinique</h4>
            <p>{s.diagnostic_summary}</p>
        </div>
        """, unsafe_allow_html=True)

    if s.interim_care:
        st.markdown(f"""
        <div class="report-section">
            <h4>Recommandations intermédiaires (MCP)</h4>
            <p>{s.interim_care}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Formulaire médecin
    st.markdown('<div class="med-card"><h3>👨‍⚕️ Revue médecin traitant</h3>', unsafe_allow_html=True)

    physician_review = st.text_area(
        "Observations cliniques",
        placeholder="Ajoutez vos observations, corrections ou précisions diagnostiques...",
        height=120,
        key="physician_review_input",
    )
    treatment_plan = st.text_area(
        "Plan de traitement / Conduite à tenir",
        placeholder="Prescriptions, examens complémentaires, orientation...",
        height=120,
        key="treatment_plan_input",
    )

    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col2:
        validate_btn = st.button("Valider →", use_container_width=True)

    if validate_btn:
        if not physician_review.strip() or not treatment_plan.strip():
            st.warning("Veuillez renseigner les observations et le plan de traitement.")
        else:
            s.physician_review = physician_review
            s.treatment_plan   = treatment_plan

            with st.spinner("Génération du rapport final..."):
                # Envoie la revue médecin comme réponse d'interrupt
                resume_res = api_post("/consultation/resume", {
                    "thread_id": s.thread_id,
                    "patient_answer": f"PHYSICIAN_REVIEW: {physician_review} | TREATMENT: {treatment_plan}",
                })

                # Petit délai pour laisser le graphe finir
                time.sleep(2)

                # Récupère le rapport final
                report = api_get(f"/consultation/{s.thread_id}/report")
                if report:
                    s.final_report = report.get("final_report") or (
                        f"**Synthèse :** {report.get('diagnostic_summary', '')}\n\n"
                        f"**Soins :** {report.get('interim_care', '')}\n\n"
                        f"**Revue médecin :** {physician_review}\n\n"
                        f"**Traitement :** {treatment_plan}"
                    )

            s.screen = 4
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# ÉCRAN 4 — Rapport final
# ══════════════════════════════════════════════════════════════════════════════
elif s.screen == 4:
    st.markdown('<div class="alert-success">✅ Consultation terminée — Rapport généré</div>', unsafe_allow_html=True)

    # En-tête rapport
    st.markdown(f"""
    <div class="med-card">
        <h3>📄 Rapport de consultation</h3>
        <div class="report-section">
            <h4>Patient</h4>
            <p>{s.patient_name}</p>
        </div>
        <div class="report-section">
            <h4>Motif de consultation</h4>
            <p>{s.initial_complaint}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Historique Q/R
    if s.qa_history:
        with st.expander("📝 Entretien patient (5 questions)", expanded=False):
            for i, (q, a) in enumerate(s.qa_history, 1):
                st.markdown(f"""
                <div class="qa-item">
                    <div class="qa-q">Q{i} — {q}</div>
                    <div class="qa-a">↳ {a}</div>
                </div>
                """, unsafe_allow_html=True)

    # Synthèse IA
    if s.diagnostic_summary:
        st.markdown(f"""
        <div class="report-section">
            <h4>🔬 Synthèse diagnostique IA</h4>
            <p>{s.diagnostic_summary}</p>
        </div>
        """, unsafe_allow_html=True)

    # Recommandations MCP
    if s.interim_care:
        st.markdown(f"""
        <div class="report-section">
            <h4>💊 Recommandations intermédiaires</h4>
            <p>{s.interim_care}</p>
        </div>
        """, unsafe_allow_html=True)

    # Revue médecin
    if s.physician_review:
        st.markdown(f"""
        <div class="report-section">
            <h4>👨‍⚕️ Observations médecin</h4>
            <p>{s.physician_review}</p>
        </div>
        """, unsafe_allow_html=True)

    # Traitement
    if s.treatment_plan:
        st.markdown(f"""
        <div class="report-section">
            <h4>📋 Plan de traitement</h4>
            <p>{s.treatment_plan}</p>
        </div>
        """, unsafe_allow_html=True)

    # Rapport final LangGraph (si disponible)
    if s.final_report and s.final_report not in [s.diagnostic_summary, ""]:
        with st.expander("📑 Rapport complet généré par l'agent", expanded=True):
            st.markdown(s.final_report)

    st.markdown("---")
    st.markdown('<div class="alert-warning">⚠️ Ce rapport est généré par un système académique. Il ne constitue pas un avis médical officiel.</div>', unsafe_allow_html=True)

    # Nouvelle consultation
     # ── Boutons — téléchargement AVANT nouvelle consultation ──────────────
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # ✅ Download AVANT le bouton reset (sinon session_state est vidé)
        st.download_button(
            label="⬇️ Télécharger le rapport (.pdf)",
            data=generate_report_pdf(s),
            file_name=f"rapport_{s.patient_name.replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    col4, col5, col6 = st.columns([ 1, 2, 1])
    with col5:
        # ✅ Reset séparé — APRÈS le download
        if st.button("🔄 Nouvelle consultation", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun() 









