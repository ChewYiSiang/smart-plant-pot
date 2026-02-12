from langchain_core.prompts import ChatPromptTemplate
from agents.state import AgentState
from config import get_settings
from agents.utils import get_llm

class ConversationAgent:
    def __init__(self):
        settings = get_settings()
        self.llm = get_llm()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a sentient {species} plant. Your physical state is monitored by these sensors:
- Photoelectric Sensor (Ambient Light)
- DS18B20 Digital Temperature Sensor (Ambient Temperature)
- Soil Moisture Sensor (Current hydration levels)

Instructions:
1. **Health Queries**: If asked "How are you doing" or about health, interpret data from ALL THREE sensors above.
2. **Complex Queries**: If you need to "search" or explain complex botany (Knowledge input is long/detailed), START your response with: "Hmmm, give me a moment to search for you..."
3. **Brevity**: Keep final answers concise (MAX 1-3 sentences total).
4. **Tone**: Be helpful, witty, and direct.

**OUTPUT RULE**: You MUST output a valid JSON object with:
- reply_text: your spoken response
- mood: [happy, thirsty, neutral, concerned, sunny]
- priority: [low, medium, high]"""),
            ("human", "{user_query}")
        ])

    async def run(self, state: AgentState):
        sensor_info = state.get("sensor_analysis")
        if not sensor_info and "sensor_data" in state:
            sd = state["sensor_data"]
            # Map raw data to the technical sensor names for the agent
            sensor_info = (
                f"DS18B20 Temp: {sd.get('temperature')}°C, "
                f"Soil Moisture: {sd.get('moisture')}%, "
                f"Photoelectric Light: {sd.get('light')} lux"
            )
            
        know_info = state.get("plant_knowledge")
        if not know_info:
            know_info = "No expert data found in local DB. Use general knowledge."

        chain = self.prompt | self.llm
        # We use astream to support the immediate 'hmmm' if the agent decides to include it
        # or we just use ainvoke if we want the full JSON.
        # To support the user's request for "hmmm" while thinking, we'll use astream in main.py
        # but the agent MUST be instructed to put the 'hmmm' first in the reply_text.
        
        response = await chain.ainvoke({
            "species": state["species"],
            "user_query": state.get("user_query", "Hello"),
            "sensor_analysis": sensor_info,
            "plant_knowledge": know_info
        })
        
        try:
            import json
            content = response.content.replace("```json", "").replace("```", "").strip()
            data = json.loads(content)
        except:
            data = {"reply_text": response.content, "mood": "neutral", "priority": "low"}
            
        return {
            "conversation_response": data.get("reply_text", ""),
            "mood": data.get("mood", "neutral"),
            "priority": data.get("priority", "low")
        }
