import json
from langchain_core.prompts import ChatPromptTemplate
from agents.state import AgentState
from config import get_settings
from agents.utils import get_llm

class ActionAgent:
    def __init__(self):
        settings = get_settings()
        self.llm = get_llm()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are the Action/Orchestrator Agent.
Based on the conversation and state, decide the final mood and display instructions for the device.
Output MUST be valid JSON with keys: reply_text, mood, priority.

**REPLY_TEXT RULE**: You MUST strictly preserve the input 'Text' as the 'reply_text' in your JSON output. Do not rewrite, shorten, or change it.

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
            "conversation_response": state.get("conversation_response", "No response generated"),
            "sensor_analysis": state.get("sensor_analysis", "No sensor analysis available")
        })
        
        try:
            # Simple cleanup in case LLM adds backticks
            content = response.content.replace("```json", "").replace("```", "").strip()
            data = json.loads(content)
        except:
            data = {
                "reply_text": state.get("conversation_response", ""),
                "mood": "neutral",
                "priority": "low"
            }
            
        return {
            "reply_text": data.get("reply_text", state.get("conversation_response", "")),
            "mood": data.get("mood", "neutral"),
            "priority": data.get("priority", "low")
        }
