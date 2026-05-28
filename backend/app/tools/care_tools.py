

# def get_basic_care(diagnostic_summary:str)->str:
  

#     return """
#     - Repos
#     - Hydratation
#     - Surveillance des symptômes
#     """

"""
tools/care_tools.py — Tool de recommandation intermédiaire

Cadre éthique respecté :
  - Pas de diagnostic définitif
  - Recommandations générales et prudentes uniquement
  - Le rapport mentionne explicitement la limite du système
  - Vocabulaire : "orientation clinique préliminaire", jamais "diagnostic"
"""
from langchain_core.tools import tool
from loguru import logger


@tool
def recommend_interim_care(symptoms_summary: str, severity_score: int) -> str:
    """
    Génère une recommandation intermédiaire générale et prudente.

    IMPORTANT : Ce tool NE pose PAS de diagnostic.
    Il produit uniquement des conseils généraux de bon sens.

    Args:
        symptoms_summary: Résumé des symptômes collectés
        severity_score: Score de gravité estimé (1-10) basé sur les réponses

    Returns:
        Recommandation intermédiaire structurée (non médicale)
    """
    logger.info(f"[recommend_interim_care] severity_score={severity_score}")

    # Recommandations par niveau de sévérité
    if severity_score <= 3:
        urgency = "faible"
        advice = [
            "Repos suffisant (au moins 8h de sommeil)",
            "Hydratation abondante (1,5 à 2L d'eau par jour)",
            "Surveillance des symptômes pendant 24-48h",
            "Consultation médicale si aggravation",
        ]
    elif severity_score <= 6:
        urgency = "modérée"
        advice = [
            "Repos strict recommandé",
            "Hydratation et alimentation légère",
            "Surveillance rapprochée toutes les 4-6h",
            "Consulter un médecin dans les 24h",
            "En cas d'aggravation rapide : consultation urgente",
        ]
    else:
        urgency = "élevée — consultation médicale recommandée rapidement"
        advice = [
            "Consultation médicale urgente recommandée",
            "Ne pas rester seul(e)",
            "Surveiller la respiration, la conscience et la douleur",
            "Si douleur thoracique, difficulté respiratoire : appeler le 15 (SAMU)",
        ]

    advice_text = "\n".join(f"• {item}" for item in advice)

    recommendation = (
        f"ORIENTATION CLINIQUE PRÉLIMINAIRE — Urgence {urgency.upper()}\n\n"
        f"Basé sur : {symptoms_summary}\n\n"
        f"Recommandations générales :\n{advice_text}\n\n"
        f"⚠️  Ce système ne remplace pas une consultation médicale.\n"
        f"Ces recommandations sont indicatives et non diagnostiques."
    )

    logger.info(f"[recommend_interim_care] Recommandation générée (urgence={urgency})")
    return recommendation


care_tools = [recommend_interim_care]
