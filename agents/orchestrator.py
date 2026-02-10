from agents.router_agent import RouterAgent

def create_pot_graph():
    # Initialize agents
    router_agent = RouterAgent()
    sensor_agent = SensorAgent()
    knowledge_agent = KnowledgeAgent()
    conversation_agent = ConversationAgent()
    action_agent = ActionAgent()
    
    # Create Graph
    workflow = StateGraph(AgentState)
    
    # Add Nodes
    workflow.add_node("classify_intent", router_agent.run)
    workflow.add_node("analyze_sensors", sensor_agent.run)
    workflow.add_node("apply_knowledge", knowledge_agent.run)
    workflow.add_node("generate_conversation", conversation_agent.run)
    workflow.add_node("finalize_action", action_agent.run)
    
    # Define Conditional Edges
    def route_intent(state: AgentState):
        intent = state.get("intent_tag")
        if intent == "HEALTH":
            return "sensor_path"
        elif intent in ["IDENTITY", "KNOWLEDGE", "GREETING", "JOKE", "AMBIGUOUS"]:
            return "knowledge_path"
        else:
            return "direct_path"

    # Define Edges
    workflow.set_entry_point("classify_intent")
    
    workflow.add_conditional_edges(
        "classify_intent",
        route_intent,
        {
            "sensor_path": "analyze_sensors",
            "knowledge_path": "apply_knowledge",
            "direct_path": "generate_conversation"
        }
    )
    
    workflow.add_edge("analyze_sensors", "apply_knowledge")
    workflow.add_edge("apply_knowledge", "generate_conversation")
    workflow.add_edge("generate_conversation", "finalize_action")
    workflow.add_edge("finalize_action", END)
    
    return workflow.compile()
