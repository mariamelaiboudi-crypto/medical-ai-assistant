# from typing import Annotated 
# from typing_extensions import TypedDict,Literal
# from langgraph.graph.message import add_messages

# class MedicalState(TypedDict,total=False):
#     messages:Annotated[list,add_messages]
#     next:Literal[
#         "diagnostic_agent",
#         "physician_review",
#         "report_agent",
#         "FINISH"
#         ]
#     question_count:int
#     interim_care: str
#     diagnostic_summary:str
#     physician_treatment: str
#     final_report:str

from typing import Literal
from langgraph.graph import MessagesState  # ← nouveau import

class MedicalState(MessagesState, total=False):  # ← hériter MessagesState
    next: Literal[
        "diagnostic_agent",
        "physician_review",
        "report_agent",
        "FINISH"
    ]
    question_count: int
    interim_care: str
    diagnostic_summary: str
    physician_treatment: str
    final_report: str 