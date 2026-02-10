from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.sensor_agent import SensorAgent
from agents.knowledge_agent import KnowledgeAgent
from agents.conversation_agent import ConversationAgent
from agents.orchestrator_agent import ActionAgent

def create_pot_graph():
    # Initialize agents
    sensor_agent = SensorAgent()
    knowledge_agent = KnowledgeAgent()
    conversation_agent = ConversationAgent()
    action_agent = ActionAgent()
    
    # Create Graph
    workflow = StateGraph(AgentState)
    
    # Add Nodes
    workflow.add_node("analyze_sensors", sensor_agent.run)
    workflow.add_node("apply_knowledge", knowledge_agent.run)
    workflow.add_node("generate_conversation", conversation_agent.run)
    workflow.add_node("finalize_action", action_agent.run)
    
    # Define Edges
    workflow.set_entry_point("analyze_sensors")
    workflow.add_edge("analyze_sensors", "apply_knowledge")
    workflow.add_edge("apply_knowledge", "generate_conversation")
    workflow.add_edge("generate_conversation", "finalize_action")
    workflow.add_edge("finalize_action", END)
    
    return workflow.compile()
