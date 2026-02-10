import asyncio
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.router_agent import RouterAgent
from agents.sensor_agent import SensorAgent
from agents.knowledge_agent import KnowledgeAgent
from agents.conversation_agent import ConversationAgent
from agents.state import AgentState

async def test_agent_flow(query, species="Basil", sensor_data=None):
    if sensor_data is None:
        sensor_data = {"temperature": 22.0, "moisture": 30.0, "light": 60.0}
    
    state: AgentState = {
        "device_id": "test_device",
        "species": species,
        "user_query": query,
        "sensor_data": sensor_data,
        "intent_tag": None,
        "sensor_analysis": None,
        "plant_knowledge": None,
        "conversation_response": None,
        "reply_text": "",
        "mood": "",
        "icons": [],
        "priority": ""
    }

    print(f"\n--- TESTING QUERY: '{query}' ({species}) ---")

    # 1. Router
    print("\n[Node: Router]")
    router = RouterAgent()
    res = router.run(state)
    state.update(res)
    print(f"Detected Intent: {state['intent_tag']}")

    # 2. Sensor (Conditional)
    if state["intent_tag"] == "HEALTH":
        print("\n[Node: Sensor]")
        sensor = SensorAgent()
        res = sensor.run(state)
        state.update(res)
        print(f"Sensor Analysis: {state['sensor_analysis']}")
    else:
        print("\n[Node: Sensor] SKIPPED")

    # 3. Knowledge
    if state["intent_tag"] in ["HEALTH", "IDENTITY", "KNOWLEDGE", "GREETING", "JOKE", "AMBIGUOUS"]:
        print("\n[Node: Knowledge]")
        knowledge = KnowledgeAgent()
        res = knowledge.run(state)
        state.update(res)
        print(f"Expert Knowledge: {state['plant_knowledge']}")

    # 4. Conversation
    print("\n[Node: Conversation]")
    conversation = ConversationAgent()
    res = conversation.run(state)
    state.update(res)
    print(f"Bot Reply: {state['conversation_response']}")

if __name__ == "__main__":
    async def main():
        # Test Cases
        await test_agent_flow("Who are you?")
        # await test_agent_flow("How are you feeling?", sensor_data={"temperature": 25, "moisture": 10, "light": 50})
        # await test_agent_flow("Where do you come from?", species="Lavender")
        # await test_agent_flow("Tell me a joke!")

    asyncio.run(main())
