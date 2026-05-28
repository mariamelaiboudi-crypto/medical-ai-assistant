# """
# backend/app/api.py — FastAPI pour le graphe médical LangGraph
# """
# import os
# import uuid
# from typing import Optional
# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from dotenv import load_dotenv
# from loguru import logger

# load_dotenv()
# # ── LangGraph client ───────────────────────────────────────────────────────────
# from langgraph_sdk import get_client
# LANGGRAPH_URL= os.getenv("LANGGRAPH_URL", "http://localhost:2024")
# GRAPH_NAME    = os.getenv("GRAPH_NAME", "medical_graph")
# def get_lg_client():
#     return get_client(url=LANGGRAPH_URL)
# # ── App ────────────────────────────────────────────────────────────────────────
# app=FastAPI(
#     title="Medical Assistant API",
#     description="API FastAPI pour le système multi-agents médical",
#     version="1.0.0",
# )
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # ── Schémas Pydantic ───────────────────────────────────────────────────────────
# class StartSessionRequest(BaseModel):
#     patient_name: Optional[str] = "Patient"
#     metadata: Optional[dict] = {}

# class StartSessionResponse(BaseModel):
#     session_id: str
#     message: str

# class StartConsultationRequest(BaseModel):
#     session_id: str
#     initial_complaint: str  # Motif de consultation initial

# class ConsultationResponse(BaseModel):
#     thread_id: str
#     status: str             # "pending_answer" | "physician_review" | "completed"
#     question: Optional[str] = None
#     question_index: Optional[int] = None
#     total_questions: Optional[int] = None
#     message: Optional[str] = None

# class ResumeConsultationRequest(BaseModel):
#     thread_id: str
#     patient_answer: str

# class ConsultationStatusResponse(BaseModel):
#     thread_id: str
#     status: str
#     question_count: int
#     diagnostic_summary: Optional[str] = None
#     interim_care: Optional[str] = None
#     physician_review: Optional[str] = None
#     treatment_plan: Optional[str] = None
#     final_report: Optional[str] = None

# class ReportResponse(BaseModel):
#     thread_id: str
#     diagnostic_summary: Optional[str] = None
#     interim_care: Optional[str] = None
#     physician_review: Optional[str] = None
#     treatment_plan: Optional[str] = None
#     final_report: Optional[str] = None
#     severity_score: Optional[int] = None

# # ── Sessions en mémoire (simple) ───────────────────────────────────────────────
# _sessions : dict[str , dict] = {}

# # ── Endpoints ─────────────────────────────────────────────────────────────────
# @app.get("/health")
# def health_check():
#     return {"status":"ok","service":"Medical Assistant API"}

# @app.post("/start_session", response_model=StartSessionResponse)
# def start_session(request: StartSessionRequest):
#     session_id=str(uuid.uuid4())
#     _sessions[session_id]={


#         "patient_name":request.patient_name,
#         "metadata":request.metadata,
#         "thread_id":None,
#         "status":"session_started",
#     }
#     return StartSessionResponse(
#         session_id=session_id,
#         message=f"Session démarrée pour {request.patient_name} (ID: {session_id})"
#     )

# @app.post("/start_consultation", response_model=ConsultationResponse)
# async def start_consultation(request: StartConsultationRequest):
#     if request.session_id not in _sessions:
#          raise HTTPException(status_code=404, detail="Session non trouvée")
    
#     client= get_lg_client()
#     thread = await client.threads.create()
#     thread_id= thread["thread_id"]

#      # associe le thread a la session
#     _sessions[request.session_id]["thread_id"]= thread_id
#          # Lance le graphe avec la plainte initiale
#     run_input = {
#         "messages": [{"role": "user", "content": request.initial_complaint}],
#         "question_count": 0,
#     }
     
#     try:
#         # stream jusqu'à l'interrupt
#         async for chunk in client.runs.stream(
#             thread_id=thread_id,
#             assistant_id=GRAPH_NAME,
#             input=run_input,
#             stream_mode="updates",
#         ):
#             logger.debug(f"chunk: {chunk}")  # on consomme le stream jusqu'à l'interrupt

#     except Exception as e:
#             logger.error(f"Error occurred: {e}")        

#     # Récupère l'état courant pour extraire la question
#     state = await client.threads.get_state(thread_id=thread_id)
#     interrupt_data = _extract_interrupt(state)

#     if interrupt_data:
#         return ConsultationResponse(
#             thread_id=thread_id,
#             status="pending_answer",
#             question=interrupt_data.get("question"),
#             question_index=interrupt_data.get("question_index"),
#             total_questions=interrupt_data.get("total", 5),
#         )

#     return ConsultationResponse(
#         thread_id=thread_id,
#         status="completed",
#         message="Consultation terminée sans questions"
#     )
# @app.post("/consultation/resume", response_model=ConsultationResponse)
# async def resume_consultation(req: ResumeConsultationRequest):
#     """
#     Reprend la consultation après la réponse du patient à une question.
#     Envoie la réponse comme valeur de resume de l'interrupt.
#     """
#     client = get_lg_client()

#     try:
#         async for chunk in client.runs.stream(
#             thread_id=req.thread_id,
#             assistant_id=GRAPH_NAME,
#             input=None,
#             command={"resume": req.patient_answer},
#             stream_mode="updates",
#         ):
#             logger.debug(f"chunk: {chunk}")
#     except Exception as e:
#         logger.error(f"Error occurred: {e}")
#         pass

#     # Vérifie l'état après reprise
#     state = await client.threads.get_state(thread_id=req.thread_id)
#     logger.debug(f"State after resume: {state}")
#     interrupt_data = _extract_interrupt(state)
#     values = state.get("values", {})

#     # Encore une question ?
#     if interrupt_data:
#         return ConsultationResponse(
#             thread_id=req.thread_id,
#             status="pending_answer",
#             question=interrupt_data.get("question"),
#             question_index=interrupt_data.get("question_index"),
#             total_questions=interrupt_data.get("total", 5),
#         )

#     # Physician review en attente ?
#     if values.get("diagnostic_summary") and not values.get("final_report"):
#         return ConsultationResponse(
#             thread_id=req.thread_id,
#             status="physician_review",
#             message="En attente de la revue médecin"
#         )

#     # Terminé
#     return ConsultationResponse(
#         thread_id=req.thread_id,
#         status="completed",
#         message="Consultation terminée"
#     )
# @app.get("/consultation/{thread_id}/report", response_model=ReportResponse)
# async def get_report(thread_id: str):
#     """Retourne le rapport final de consultation."""
#     client = get_lg_client()

#     try:
#         state = await client.threads.get_state(thread_id=thread_id)
#     except Exception as e:
#         raise HTTPException(status_code=404, detail=f"Thread introuvable : {e}")

#     values = state.get("values", {})

#     if not values.get("final_report") and not values.get("diagnostic_summary"):
#         raise HTTPException(
#             status_code=202,
#             detail="Rapport non encore disponible — consultation en cours"
#         )

#     return ReportResponse(
#         thread_id=thread_id,
#         diagnostic_summary=values.get("diagnostic_summary"),
#         interim_care=values.get("interim_care"),
#         physician_review=values.get("physician_review"),
#         treatment_plan=values.get("treatment_plan"),
#         final_report=values.get("final_report"),
#     )
# # @app.get("/consultation/{thread_id}", response_model=ConsultationStatusResponse)
# # async def get_consultation_status(thread_id: str):
# #     """Retourne l'état courant de la consultation."""
# #     client = get_lg_client()

# #     try:
# #         state = await client.threads.get_state(thread_id=thread_id)
# #     except Exception as e:
# #         raise HTTPException(status_code=404, detail=f"Thread introuvable : {e}")

# #     values = state.get("values", {})
# #     interrupt_data = _extract_interrupt(state)

# #     # Détermine le statut
# #     if interrupt_data:
# #         status = "pending_answer"
# #     elif values.get("final_report"):
# #         status = "completed"
# #     elif values.get("diagnostic_summary"):
# #         status = "physician_review"
# #     else:
# #         status = "in_progress"

# #     return ConsultationStatusResponse(
# #         thread_id=thread_id,
# #         status=status,
# #         question_count=values.get("question_count", 0),
# #         diagnostic_summary=values.get("diagnostic_summary"),
# #         interim_care=values.get("interim_care"),
# #         physician_review=values.get("physician_review"),
# #         treatment_plan=values.get("treatment_plan"),
# #         final_report=values.get("final_report"),
# #     )


# @app.get("/consultation/{thread_id}", response_model=ConsultationStatusResponse)
# async def get_consultation_status(thread_id: str):
#     client = get_lg_client()

#     try:
#         state = await client.threads.get_state(thread_id=thread_id)
#         logger.debug(f"State type: {type(state)}, State: {state}")
#     except Exception as e:
#         raise HTTPException(status_code=404, detail=f"Thread introuvable : {e}")

#     # langgraph_sdk retourne un objet ThreadState, pas un dict
#     # on accède aux valeurs via .values ou via dict
#     try:
#         values = state.values if hasattr(state, "values") else state.get("values", {})
#         tasks  = state.tasks  if hasattr(state, "tasks")  else state.get("tasks", [])
#     except Exception as e:
#         logger.error(f"State parse error: {e} — state={state}")
#         raise HTTPException(status_code=500, detail=f"Erreur lecture état : {e}")

#     interrupt_data = _extract_interrupt_from(tasks)

#     if interrupt_data:
#         status = "pending_answer"
#     elif values.get("final_report"):
#         status = "completed"
#     elif values.get("diagnostic_summary"):
#         status = "physician_review"
#     else:
#         status = "in_progress"

#     return ConsultationStatusResponse(
#         thread_id=thread_id,
#         status=status,
#         question_count=values.get("question_count", 0),
#         diagnostic_summary=values.get("diagnostic_summary"),
#         interim_care=values.get("interim_care"),
#         physician_review=values.get("physician_review"),
#         treatment_plan=values.get("treatment_plan"),
#         final_report=values.get("final_report"),
#     )


# # ── Helper ─────────────────────────────────────────────────────────────────────
# def _extract_interrupt(state: dict) -> Optional[dict]:
#     """Extrait les données d'interrupt depuis l'état LangGraph."""
#     tasks = state.get("tasks", [])
#     for task in tasks:
#         interrupts = task.get("interrupts", [])
#         for interrupt in interrupts:
#             value = interrupt.get("value", {})
#             if isinstance(value, dict) and value.get("type") == "patient_question":
#                 return value
#     return None
# def _extract_interrupt_from(tasks) -> Optional[dict]:
#     """Fonctionne avec tasks comme liste d'objets ou de dicts."""
#     for task in tasks:
#         # Objet avec attribut
#         interrupts = getattr(task, "interrupts", None) or (
#             task.get("interrupts", []) if isinstance(task, dict) else []
#         )
#         for interrupt in interrupts:
#             value = getattr(interrupt, "value", None) or (
#                 interrupt.get("value", {}) if isinstance(interrupt, dict) else {}
#             )
#             if isinstance(value, dict) and value.get("type") == "patient_question":
#                 return value
#     return None

# # ── Lancement ──────────────────────────────────────────────────────────────────
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)



"""
backend/app/api.py — FastAPI pour le graphe médical LangGraph
"""
import os
import uuid
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

# ── LangGraph client ───────────────────────────────────────────────────────────
from langgraph_sdk import get_client

LANGGRAPH_URL = os.getenv("LANGGRAPH_URL", "http://localhost:2024")
GRAPH_NAME    = os.getenv("GRAPH_NAME", "medical_graph")

def get_lg_client():
    return get_client(url=LANGGRAPH_URL)

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Medical Assistant API",
    description="API FastAPI pour le système multi-agents médical",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Schémas Pydantic ───────────────────────────────────────────────────────────
class StartSessionRequest(BaseModel):
    patient_name: Optional[str] = "Patient"
    metadata: Optional[dict] = {}

class StartSessionResponse(BaseModel):
    session_id: str
    message: str

class StartConsultationRequest(BaseModel):
    session_id: str
    initial_complaint: str

class ConsultationResponse(BaseModel):
    thread_id: str
    status: str
    question: Optional[str] = None
    question_index: Optional[int] = None
    total_questions: Optional[int] = None
    message: Optional[str] = None

class ResumeConsultationRequest(BaseModel):
    thread_id: str
    patient_answer: str

class ConsultationStatusResponse(BaseModel):
    thread_id: str
    status: str
    question_count: int
    diagnostic_summary: Optional[str] = None
    interim_care: Optional[str] = None
    physician_review: Optional[str] = None
    treatment_plan: Optional[str] = None
    final_report: Optional[str] = None

class ReportResponse(BaseModel):
    thread_id: str
    diagnostic_summary: Optional[str] = None
    interim_care: Optional[str] = None
    physician_review: Optional[str] = None
    treatment_plan: Optional[str] = None
    final_report: Optional[str] = None
    severity_score: Optional[int] = None

# ── Sessions en mémoire ────────────────────────────────────────────────────────
_sessions: dict[str, dict] = {}


# ── Helpers ────────────────────────────────────────────────────────────────────
def _get_values(state: dict) -> dict:
    """
    state est toujours un dict retourné par langgraph_sdk.
    state['values'] contient les données du graphe.
    NE PAS faire state.values — c'est la méthode built-in du dict !
    """
    return state.get("values", {})


def _extract_text(value) -> Optional[str]:
    """
    Extrait le texte d'un champ qui peut être :
    - une str simple
    - une liste MCP : [{'type': 'text', 'text': '...'}]
    """
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, list) and value:
        first = value[0]
        if isinstance(first, dict):
            return first.get("text") or first.get("content") or str(first)
        return str(first)
    return str(value)


def _extract_interrupt(state: dict) -> Optional[dict]:
    """Extrait les données d'interrupt depuis l'état LangGraph."""
    tasks = state.get("tasks", [])
    for task in tasks:
        # task peut être un dict ou un objet
        if isinstance(task, dict):
            interrupts = task.get("interrupts", [])
        else:
            interrupts = getattr(task, "interrupts", []) or []

        for interrupt in interrupts:
            if isinstance(interrupt, dict):
                value = interrupt.get("value", {})
            else:
                value = getattr(interrupt, "value", {})

            if isinstance(value, dict) and value.get("type") == "patient_question":
                return value
    return None


# ── Endpoints ──────────────────────────────────────────────────────────────────
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Medical Assistant API"}


@app.post("/start_session", response_model=StartSessionResponse)
def start_session(request: StartSessionRequest):
    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "patient_name": request.patient_name,
        "metadata": request.metadata,
        "thread_id": None,
        "status": "session_started",
    }
    return StartSessionResponse(
        session_id=session_id,
        message=f"Session démarrée pour {request.patient_name} (ID: {session_id})"
    )


@app.post("/start_consultation", response_model=ConsultationResponse)
async def start_consultation(request: StartConsultationRequest):
    if request.session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session non trouvée")

    client = get_lg_client()
    thread = await client.threads.create()
    thread_id = thread["thread_id"]

    _sessions[request.session_id]["thread_id"] = thread_id

    run_input = {
        "messages": [{"role": "user", "content": request.initial_complaint}],
        "question_count": 0,
    }

    try:
        async for chunk in client.runs.stream(
            thread_id=thread_id,
            assistant_id=GRAPH_NAME,
            input=run_input,
            stream_mode="updates",
        ):
            logger.debug(f"chunk: {chunk}")
    except Exception as e:
        logger.error(f"[start_consultation] stream error: {e}")

    state = await client.threads.get_state(thread_id=thread_id)
    interrupt_data = _extract_interrupt(state)

    if interrupt_data:
        return ConsultationResponse(
            thread_id=thread_id,
            status="pending_answer",
            question=interrupt_data.get("question"),
            question_index=interrupt_data.get("question_index"),
            total_questions=interrupt_data.get("total", 5),
        )

    return ConsultationResponse(
        thread_id=thread_id,
        status="completed",
        message="Consultation terminée sans questions"
    )


@app.post("/consultation/resume", response_model=ConsultationResponse)
async def resume_consultation(req: ResumeConsultationRequest):
    client = get_lg_client()

    try:
        async for chunk in client.runs.stream(
            thread_id=req.thread_id,
            assistant_id=GRAPH_NAME,
            input=None,
            command={"resume": req.patient_answer},
            stream_mode="updates",
        ):
            logger.debug(f"chunk: {chunk}")
    except Exception as e:
        logger.error(f"[resume] stream error: {e}")

    state = await client.threads.get_state(thread_id=req.thread_id)
    interrupt_data = _extract_interrupt(state)
    values = _get_values(state)  # ✅ state.get("values", {}) — PAS state.values

    if interrupt_data:
        return ConsultationResponse(
            thread_id=req.thread_id,
            status="pending_answer",
            question=interrupt_data.get("question"),
            question_index=interrupt_data.get("question_index"),
            total_questions=interrupt_data.get("total", 5),
        )

    if values.get("diagnostic_summary") and not values.get("final_report"):
        return ConsultationResponse(
            thread_id=req.thread_id,
            status="physician_review",
            message="En attente de la revue médecin"
        )

    return ConsultationResponse(
        thread_id=req.thread_id,
        status="completed",
        message="Consultation terminée"
    )


# ⚠️ /report AVANT /{thread_id} — ordre important pour FastAPI
@app.get("/consultation/{thread_id}/report", response_model=ReportResponse)
async def get_report(thread_id: str):
    client = get_lg_client()

    try:
        state = await client.threads.get_state(thread_id=thread_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Thread introuvable : {e}")

    values = _get_values(state)  # ✅

    if not values.get("final_report") and not values.get("diagnostic_summary"):
        raise HTTPException(
            status_code=202,
            detail="Rapport non encore disponible — consultation en cours"
        )

    return ReportResponse(
        thread_id=thread_id,
        diagnostic_summary=_extract_text(values.get("diagnostic_summary")),
        interim_care=_extract_text(values.get("interim_care")),
        physician_review=_extract_text(values.get("physician_review")),
        treatment_plan=_extract_text(values.get("treatment_plan")),
        final_report=_extract_text(values.get("final_report")),
    )


@app.get("/consultation/{thread_id}", response_model=ConsultationStatusResponse)
async def get_consultation_status(thread_id: str):
    client = get_lg_client()

    try:
        state = await client.threads.get_state(thread_id=thread_id)
        logger.debug(f"state type={type(state)}")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Thread introuvable : {e}")

    values = _get_values(state)  # ✅ CORRECT — jamais state.values
    interrupt_data = _extract_interrupt(state)

    if interrupt_data:
        status = "pending_answer"
    elif values.get("final_report"):
        status = "completed"
    elif values.get("diagnostic_summary"):
        status = "physician_review"
    else:
        status = "in_progress"

    return ConsultationStatusResponse(
        thread_id=thread_id,
        status=status,
        question_count=values.get("question_count", 0),
        diagnostic_summary=_extract_text(values.get("diagnostic_summary")),
        interim_care=_extract_text(values.get("interim_care")),
        physician_review=_extract_text(values.get("physician_review")),
        treatment_plan=_extract_text(values.get("treatment_plan")),
        final_report=_extract_text(values.get("final_report")),
    )


# ── Lancement ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.api:app", host="0.0.0.0", port=8000, reload=True)




