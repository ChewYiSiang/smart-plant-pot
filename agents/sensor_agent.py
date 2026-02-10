from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from agents.state import AgentState
from config import get_settings

class SensorAgent:
    def __init__(self):
        settings = get_settings()
        self.llm = ChatGoogleGenerativeAI(google_api_key=settings.GOOGLE_API_KEY, model="gemini-2.5-pro")
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Sensor Analysis Agent for a smart plant pot.
Your job is to interpret raw sensor values (temp, moisture, light) and detect thresholds, trends, or anomalies.
Be clinical and precise. Tell us what the physical state of the plant is based on the numbers.
Current data: {sensor_data}
            """),
            ("human", "Analyze the current state of the plant.")
        ])

    def run(self, state: AgentState):
        chain = self.prompt | self.llm
        response = chain.invoke({"sensor_data": state["sensor_data"]})
        return {"sensor_analysis": response.content}
