from langchain_core.prompts import ChatPromptTemplate
from agents.state import AgentState
from config import get_settings
from agents.utils import get_llm

class SensorAgent:
    def __init__(self):
        settings = get_settings()
        self.llm = get_llm()
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
