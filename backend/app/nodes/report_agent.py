from backend.app.state import MedicalState

def report_agent(state: MedicalState):
    diagnostic_summary=state.get(
        "diagnostic_summary")
    physician_treatment=state.get(
        "physician_treatment")
    final_report=f"""
    =========Rapport final ======
    Synthèse clinique : {diagnostic_summary}
    TRAITEMENT MÉDICAL PROPOSÉ : {physician_treatment}
    ⚠️ Recommandation:
    Ceci ne remplace pas une consultation médicale.

    """
    return {
        "final_report": final_report,
         "next": "FINISH"
    }