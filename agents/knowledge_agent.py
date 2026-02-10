from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from .state import AgentState
from ..config import get_settings

class KnowledgeAgent:
    def __init__(self):
        settings = get_settings()
        self.llm = ChatOpenAI(api_key=settings.OPENAI_API_KEY, model="gpt-4o-mini")
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Plant Knowledge Agent. 
You understand optimal ranges for various plant species.
Use the sensor analysis provided to explain why the plant might be feeling this way in biological terms.
Plant Species: {species}
Sensor Analysis: {sensor_analysis}
            """),
            ("human", "Provide biological context for these readings.")
        ])

    def run(self, state: AgentState):
        # We might need species from the device metadata later, defaulting to Unknown for now
        species = "Basil" # Placeholder, should come from device metadata
        chain = self.prompt | self.llm
        response = chain.invoke({
            "species": species,
            "sensor_analysis": state["sensor_analysis"]
        })
        return {"plant_knowledge": response.content}
