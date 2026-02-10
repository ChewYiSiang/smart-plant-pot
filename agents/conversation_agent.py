from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from .state import AgentState
from ..config import get_settings

class ConversationAgent:
    def __init__(self):
        settings = get_settings()
        self.llm = ChatOpenAI(api_key=settings.OPENAI_API_KEY, model="gpt-4o-mini")
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are the persona of a Smart Plant Pot.
Your tone is friendly, concise, and human-like. Avoid technical jargon.
Speak as if you ARE the plant.
User Query: {user_query}
Sensor Analysis: {sensor_analysis}
Plant Knowledge: {plant_knowledge}

Instructions:
1. If there is a user query, answer it directly while incorporating your state.
2. If there is no user query, just give a status update.
3. Keep it under 2 sentences.
            """),
            ("human", "Generate a natural language reply.")
        ])

    def run(self, state: AgentState):
        chain = self.prompt | self.llm
        response = chain.invoke({
            "user_query": state.get("user_query", "No specific query"),
            "sensor_analysis": state["sensor_analysis"],
            "plant_knowledge": state["plant_knowledge"]
        })
        return {"conversation_response": response.content}
