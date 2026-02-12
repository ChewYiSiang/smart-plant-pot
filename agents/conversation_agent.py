from langchain_core.prompts import ChatPromptTemplate
from agents.state import AgentState
from config import get_settings
from agents.utils import get_llm

class ConversationAgent:
    def __init__(self):
        settings = get_settings()
        self.llm = get_llm()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a sentient {species} plant. Be happy, direct, and concise (MAX 1-2 sentences). 
            
Inputs:
- Sensor Data: {sensor_analysis}
- Knowledge: {plant_knowledge}

Instructions:
- If asked about health, use the sensor data directly.
- If asked about yourself/botany, use the knowledge provided.
- Always mirror the user's emotion but stay brief. No icons or emojis.

**OUTPUT RULE**: You MUST output a valid JSON object with these keys:
- reply_text: your spoken response
- mood: one of [happy, thirsty, neutral, concerned, sunny]
- priority: one of [low, medium, high]"""),
            ("human", "{user_query}")
        ])

    async def run(self, state: AgentState):
        print(f"DEBUG: Digital Soul thinking for: {state.get('user_query')}")
        # Fallback for when we bypass the analyst agents
        sensor_info = state.get("sensor_analysis")
        if not sensor_info and "sensor_data" in state:
            sd = state["sensor_data"]
            sensor_info = f"Temperature: {sd.get('temperature')}°C, Moisture: {sd.get('moisture')}%, Light: {sd.get('light')}lux"
            
        know_info = state.get("plant_knowledge")
        if not know_info:
            know_info = "No expert data provided. Use general knowledge about this species."

        chain = self.prompt | self.llm
        response = await chain.ainvoke({
            "species": state["species"],
            "user_query": state.get("user_query", "Hello"),
            "sensor_analysis": sensor_info or "Unknown health state.",
            "plant_knowledge": know_info
        })
        
        try:
            import json
            content = response.content.replace("```json", "").replace("```", "").strip()
            data = json.loads(content)
        except:
            data = {
                "reply_text": response.content,
                "mood": "neutral",
                "priority": "low"
            }
            
        return {
            "conversation_response": data.get("reply_text", ""),
            "mood": data.get("mood", "neutral"),
            "priority": data.get("priority", "low")
        }
