"""
nodes/diagnostic_agent.py — VERSION MCP CORRECTE
"""
import os
import json
import re
from loguru import logger
from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import interrupt
from dotenv import load_dotenv

from backend.app.state import MedicalState
from backend.app.tools.mcp_client import  invoke_tool_sync  # ✅ MCP

load_dotenv()


def _get_llm():
    """LLM isolé — facilement swappable."""
    return ChatGroq(
        model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
        temperature=0,
        api_key=os.getenv("GROQ_API_KEY")
    )



def DiagnosticAgent(state: MedicalState) -> dict:
    messages       = state.get("messages", [])
    question_count = state.get("question_count", 0)
    llm            = _get_llm()

    # ──────────────────────────────────────────
    # ÉTAPE 1 — Questions via MCP
    # ──────────────────────────────────────────
    if question_count < 5:
        try:
         question_text = invoke_tool_sync("ask_patient", {"question_index": question_count})

        except Exception as e:
            logger.error(f"[DiagnosticAgent] ask_patient error : {e}")
            question_text = "Pouvez-vous décrire vos symptômes ?"
            
        if isinstance(question_text, list):
           text = question_text[0].get("text", "")
        elif isinstance(question_text, dict):
           text = question_text.get("text", "")
        else:
           text = str(question_text)

        logger.info(
          f"[DiagnosticAgent] Question {question_count + 1}/5 : {text}"
    )

        patient_answer = interrupt({
            "type": "patient_question",
            "question": text,
            "question_index": question_count,
            "total": 5,
    })
        

        return {
            "messages": messages + [
                AIMessage(content=text),
                HumanMessage(content=str(patient_answer)),
            ],
            "question_count": question_count + 1,
            "next": "supervisor",
        }

    # ──────────────────────────────────────────
    # ÉTAPE 2 — Synthèse + Recommandation MCP
    # ──────────────────────────────────────────
    conversation = "\n".join(
        f"{'Médecin' if isinstance(m, AIMessage) else 'Patient'}: {m.content}"
        for m in messages
    )

    # Prompt JSON structuré — plus fiable que le parsing regex
    summary_prompt = f"""
    Tu es un assistant d'orientation clinique préliminaire (exercice académique).

    Entretien patient :
    {conversation}

    Réponds UNIQUEMENT en JSON valide, sans texte avant ou après :
    {{
        "synthese": "synthèse clinique factuelle courte",
        "score": 5
    }}

    score = entier entre 1 (bénin) et 10 (critique).
    Pas de diagnostic définitif.
    """

    response = llm.invoke(summary_prompt)

    # Parse JSON — robuste
    try:
        clean = response.content.strip().strip("```json").strip("```")
        data = json.loads(clean)
        diagnostic_summary = data["synthese"]
        severity_score = max(1, min(int(data["score"]), 10))
    except Exception as e:
        logger.warning(f"[DiagnosticAgent] JSON parse error : {e}")
        diagnostic_summary = response.content
        severity_score = _extract_severity_fallback(response.content)

    # Tool recommend_interim_care via MCP
    try:
# Et :
        interim_care = invoke_tool_sync("recommend_interim_care", {
            "symptoms_summary": diagnostic_summary,
            "severity_score": severity_score,
        })
    except Exception as e:
        logger.error(f"[DiagnosticAgent] recommend_interim_care error : {e}")
        interim_care = "Recommandation indisponible. Consultez un médecin."

    logger.info(
        f"[DiagnosticAgent] Synthèse OK — score={severity_score}"
    )

    return {
        "diagnostic_summary": diagnostic_summary,
        "interim_care": interim_care,
        "next": "supervisor",
    }


def _extract_severity_fallback(text: str) -> int:
    """Fallback si le LLM ne répond pas en JSON."""
    match = re.search(r'SCORE\s*:\s*(\d+)', text, re.IGNORECASE)
    if match:
        return min(int(match.group(1)), 10)
    text_lower = text.lower()
    if any(w in text_lower for w in ["urgent", "grave", "critique"]):
        return 7
    if any(w in text_lower for w in ["modéré", "moyen"]):
        return 4
    return 2