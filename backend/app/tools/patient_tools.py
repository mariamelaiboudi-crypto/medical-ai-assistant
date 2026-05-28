from langgraph.types import  interrupt



# def ask_patient(question:str)->str:

#     """
#     Simule une interaction avec le patient.
#     Dans une vraie application, cela pourrait être une interface utilisateur ou une API.
#     """
#     print(f"Question pour le patient : {question}")
#     # Simuler la réponse du patient (dans une vraie application, on attendrait une réponse réelle)
#     # answer = input("\nRéponse patient : ") # ← terminal peut gérer ça !
#     answer = interrupt({"question": question})  # ← Studio peut gérer ça !
#     return answer


# tools/patient_tools.py — VERSION CORRIGÉE
from langchain_core.tools import tool
from loguru import logger

CLINICAL_QUESTIONS = [
    "Depuis combien de temps ressentez-vous ces symptômes ?",
    "Pouvez-vous décrire l'intensité de votre douleur ou gêne sur une échelle de 1 à 10 ?",
    "Avez-vous de la fièvre ou des frissons ? Si oui, quelle température ?",
    "Avez-vous pris des médicaments récemment ? Lesquels ?",
    "Avez-vous des antécédents médicaux ou des allergies connues ?",
]

@tool
def ask_patient(question_index: int) -> str:
    """Retourne le texte de la question clinique à poser au patient (index 0 à 4)."""
    if 0 <= question_index < len(CLINICAL_QUESTIONS):
        return CLINICAL_QUESTIONS[question_index]
    return "Toutes les questions ont été posées."

# ❌ RETIRÉ : interrupt() ne va PAS ici
# interrupt() doit être dans le NODE qui gère le HITL,
# car LangGraph ne peut suspendre que depuis un node, pas depuis un tool.

patient_tools = [ask_patient]