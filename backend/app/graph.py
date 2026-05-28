from backend.app.state import MedicalState
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from backend.app.nodes.diagnostic_agent import DiagnosticAgent
from backend.app.nodes.physician_agent import physician_review
from backend.app.nodes.supervisor import supervisor, supervisor_router
from backend.app.nodes.report_agent import report_agent
from loguru import logger
import os

logger.info("Initialisation du graphe médical...")

workflow = StateGraph(MedicalState)
workflow.add_node("supervisor", supervisor)
workflow.add_node("diagnostic_agent", DiagnosticAgent)
workflow.add_node("physician_review", physician_review)
workflow.add_node("report_agent", report_agent)

workflow.add_edge(START, "supervisor")
workflow.add_conditional_edges(
    "supervisor",
    supervisor_router,
    {
        "diagnostic_agent": "diagnostic_agent",
        "physician_review": "physician_review",
        "report_agent": "report_agent",
        "FINISH": END
    }
)
workflow.add_edge("diagnostic_agent", "supervisor")
workflow.add_edge("physician_review", "supervisor")
workflow.add_edge("report_agent", "supervisor")

# db_path = os.getenv("SQLITE_DB_PATH", "./data/checkpoints.db")
# os.makedirs(os.path.dirname(db_path), exist_ok=True)
# checkpointer = SqliteSaver.from_conn_string(db_path).__enter__()

graph = workflow.compile(
    # checkpointer=checkpointer,
    interrupt_before=["physician_review"],
)

logger.info("Graphe compilé avec succès !")