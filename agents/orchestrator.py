from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.conversation_agent import ConversationAgent
from sqlmodel import Session, select
from models import get_engine, PlantKnowledge

def fast_find_knowledge(species: str):
    """Sync check for plant knowledge in local DB."""
    try:
        engine = get_engine()
        with Session(engine) as session:
            statement = select(PlantKnowledge).where(PlantKnowledge.species == species)
            return session.exec(statement).first()
    except Exception:
        return None

def create_pot_graph():
    # Only one agent needed for the simplified graph to reduce latency
    digital_soul = ConversationAgent()
    
    workflow = StateGraph(AgentState)
    
    # Single node architecture: Interprets context and generates response in one pass
    workflow.add_node("generate_conversation", digital_soul.run)
    
    workflow.set_entry_point("generate_conversation")
    workflow.add_edge("generate_conversation", END)
    
    return workflow.compile()
