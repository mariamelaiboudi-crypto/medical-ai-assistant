"""
mcp_server/server.py — Serveur MCP médical académique
"""
import logging
from mcp.server.fastmcp import FastMCP
from pydantic import Field

# Logger correct
logger = logging.getLogger(__name__)

# Serveur MCP
mcp = FastMCP(
    name="medical-clinical-tools",
)

# Questions cliniques
CLINICAL_QUESTIONS = [
    "Depuis combien de temps ressentez-vous ces symptômes ?",
    "Pouvez-vous décrire l'intensité de votre douleur sur une échelle de 1 à 10 ?",
    "Avez-vous de la fièvre ? Si oui, quelle température ?",
    "Avez-vous pris des médicaments récemment ? Lesquels ?",
    "Avez-vous des antécédents médicaux ou des allergies connues ?",
]

@mcp.tool()
def ask_patient(
    question_index: int = Field(ge=0, le=4, description="Index de la question (0 à 4)")
) -> str:
    """
    Retourne une question clinique à poser au patient.
    Appeler séquentiellement de 0 à 4 pour collecter tous les symptômes.
    """
    if 0 <= question_index < len(CLINICAL_QUESTIONS):
        logger.info(f"[ask_patient] Question {question_index} demandée")
        return CLINICAL_QUESTIONS[question_index]
    return "Toutes les questions ont été posées."


@mcp.tool()
def recommend_interim_care(
    symptoms_summary: str = Field(description="Résumé des symptômes collectés"),
    severity_score: int = Field(ge=1, le=10, description="Score de gravité (1=faible, 10=critique)")
) -> str:
    """
    Génère une recommandation intermédiaire générale et prudente.
    NE pose PAS de diagnostic. Produit uniquement des conseils de bon sens.
    """
    logger.info(f"[recommend_interim_care] severity_score={severity_score}")

    if severity_score <= 3:
        urgency = "FAIBLE"
        advice = [
            "Repos suffisant (au moins 8h de sommeil)",
            "Hydratation abondante (1,5 à 2L d'eau par jour)",
            "Surveillance des symptômes pendant 24-48h",
            "Consultation médicale si aggravation",
        ]
    elif severity_score <= 6:
        urgency = "MODÉRÉE"
        advice = [
            "Repos strict recommandé",
            "Hydratation et alimentation légère",
            "Surveillance rapprochée toutes les 4-6h",
            "Consulter un médecin dans les 24h",
        ]
    else:
        urgency = "ÉLEVÉE"
        advice = [
            "Consultation médicale urgente recommandée",
            "Ne pas rester seul(e)",
            "Surveiller respiration, conscience et douleur",
            "Si douleur thoracique ou difficulté respiratoire : appeler le 15",
        ]

    advice_text = "\n".join(f"• {item}" for item in advice)

    return (
        f"ORIENTATION CLINIQUE — Urgence {urgency}\n\n"
        f"Basé sur : {symptoms_summary}\n\n"
        f"Recommandations :\n{advice_text}\n\n"
        f"⚠️ Ce système ne remplace pas une consultation médicale."
    )


if __name__ == "__main__":
    import uvicorn
    print("MCP Server démarré sur http://localhost:8001 ...")
    app = mcp.sse_app()  # expose l'app ASGI
    uvicorn.run(app, host="localhost", port=8001)