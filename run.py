from backend.app.graph import graph
from langgraph.types import Command

config = {"configurable": {"thread_id": "medical-session-1"}}
initial_state = {"question_count": 0, "messages": []}

# Tour 1
for step in graph.stream(initial_state, config=config):
    print(step)

# Tour 2 — validation médecin
physician_input = input("\nMédecin, entrez votre traitement : ")
for step in graph.stream(Command(resume=physician_input), config=config):
    print(step)