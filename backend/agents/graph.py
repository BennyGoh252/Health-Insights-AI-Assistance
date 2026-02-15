from langgraph.graph import StateGraph
from backend.app.state import AgentState
from backend.agents.followup_agent import followup_agent

def build_graph():

    workflow = StateGraph(AgentState)

    workflow.add_node("followup", followup_agent)

    workflow.set_entry_point("followup")
    workflow.set_finish_point("followup")

    return workflow.compile()