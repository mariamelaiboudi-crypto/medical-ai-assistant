from backend.app.state import MedicalState
from loguru import logger


def supervisor(state: MedicalState):

    # Nombre questions posées
    question_count = state.get(
        "question_count",
        0
    )

    # Vérifie si synthèse clinique existe
    interim_care = state.get(
        "interim_care"
    )

    # Vérifie si traitement médecin existe
    physician_treatment = state.get(
        "physician_treatment"
    )

    # Vérifie si rapport final existe
    final_report = state.get(
        "final_report"
    )
    diagnostic_summary = state.get(
        "diagnostic_summary"
    )

    # --------------------------------
    # ETAPE 1 : Continuer diagnostic
    # --------------------------------
    logger.info(
    f"[Supervisor] Q={question_count} | "
    f"diag={bool(diagnostic_summary)} | "
    f"care={bool(interim_care)} | "
    f"treatment={bool(physician_treatment)} | "
    f"final={bool(final_report)}"
)
    if final_report:

        return {
            "next": "FINISH"
        }
    elif physician_treatment:

        return {
            "next": "report_agent"
        }
    elif interim_care and diagnostic_summary:

        return {
            "next": "physician_review"
        }
    else:

        return {
            "next": "diagnostic_agent"
        }




    

def supervisor_router(state: MedicalState):

    decision = supervisor(state)


    return decision["next"]