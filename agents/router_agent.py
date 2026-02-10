from langchain_core.prompts import ChatPromptTemplate
from agents.state import AgentState
from config import get_settings
from agents.utils import get_llm

class RouterAgent:
    def __init__(self):
        settings = get_settings()
        self.llm = get_llm()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are the Intent Router for a Smart Plant Pot.
Your job is to categorize the user's query into one of the following tags:

- **IDENTITY**: Asking about who/what the plant is, its name, or its personality (e.g., "tell me about yourself", "who are you").
- **HEALTH**: Asking about the plant's well-being, needs, or current state (e.g., "how are you?", "do you need water?").
- **KNOWLEDGE**: Asking for specific botanical facts or care instructions unrelated to current state (e.g., "where do cacti come from?").
- **GREETING**: Asking for a greeting (e.g., "hello", "hi").
- **JOKE**: Asking for a joke (e.g., "tell me a joke").
- **AMBIGUOUS**: The query is unclear or too short to categorize.

Output ONLY the tag name in uppercase.

User Query: {user_query}
"""),
            ("human", "Classify this query.")
        ])

    def run(self, state: AgentState):
        if not state.get("user_query"):
            return {"intent_tag": "HEALTH"} # Default to health check for heartbeat
            
        chain = self.prompt | self.llm
        response = chain.invoke({"user_query": state["user_query"]})
        tag = response.content.strip().upper()
        
        # Validation
        valid_tags = ["IDENTITY", "HEALTH", "KNOWLEDGE", "GREETING", "JOKE", "AMBIGUOUS"]
        if tag not in valid_tags:
            tag = "AMBIGUOUS"
            
        return {"intent_tag": tag}
