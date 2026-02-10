import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from agents.state import AgentState
from config import get_settings

class ActionAgent:
    def __init__(self):
        settings = get_settings()
        self.llm = ChatGoogleGenerativeAI(google_api_key=settings.GOOGLE_API_KEY, model="gemini-2.5-pro")
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are the Action/Orchestrator Agent.
Based on the conversation and state, decide the final mood and display instructions for the device.
Output MUST be valid JSON with keys: reply_text, mood, icons, priority.

Available Moods: happy, thirsty, neutral, concerned, sunny
Priority: low, medium, high

Input:
Text: {conversation_response}
Sensor Analysis: {sensor_analysis}
            """),
            ("human", "Produce the final response object.")
        ])

    def run(self, state: AgentState):
        chain = self.prompt | self.llm
        response = chain.invoke({
            "conversation_response": state["conversation_response"],
            "sensor_analysis": state["sensor_analysis"]
        })
        
        try:
            # Simple cleanup in case LLM adds backticks
            content = response.content.replace("```json", "").replace("```", "").strip()
            data = json.loads(content)
        except:
            data = {
                "reply_text": state["conversation_response"],
                "mood": "neutral",
                "icons": [],
                "priority": "low"
            }
            
        return {
            "reply_text": data.get("reply_text", state["conversation_response"]),
            "mood": data.get("mood", "neutral"),
            "icons": data.get("icons", []),
            "priority": data.get("priority", "low")
        }
