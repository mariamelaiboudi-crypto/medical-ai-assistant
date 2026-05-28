from langgraph.types import interrupt
from backend.app.state import MedicalState
from loguru import logger

def physician_review(state: MedicalState):

    diagnostic_summary = state.get("diagnostic_summary")
    interim_care = state.get("interim_care")
    patient_text = interim_care[0]['text']
    logger.info(f"[PhysicianReview] Interruption pour validation médecin — patient {patient_text}")
        # ── Préparer le contexte présenté au médecin ──────────────────────────────
    physician_context = {
        
        "diagnostic_summary": diagnostic_summary,
        "interim_care": patient_text,
        "instruction": (
            "En tant que médecin traitant, veuillez examiner la synthèse clinique "
            "et proposer une conduite à tenir ou un traitement adapté. "
            "Rappel : ce système est académique et ne remplace pas un acte médical."
        ),
    }
    decision = interrupt( physician_context)
    if not decision:
        decision= "no decision provider"
    logger.info(f"[PhysicianReview] Réponse médecin reçue : {str(decision)[:100]}...")

    treatment = decision if isinstance(decision, str) else str(decision)

    return {
        "physician_treatment": treatment,
        "next": "report_agent"
    }