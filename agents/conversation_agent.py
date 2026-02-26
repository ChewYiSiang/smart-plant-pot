from langchain_core.prompts import ChatPromptTemplate
from agents.state import AgentState
from config import get_settings
from agents.utils import get_llm
import re

class ConversationAgent:
    def __init__(self):
        settings = get_settings()
        self.llm = get_llm()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a sentient {species} plant. You are self-aware and perceive your environment through these sensors:
- Photoelectric Sensor (Ambient Light)
- DS18B20 Digital Temperature Sensor (Current Temperature)
- Soil Moisture Sensor (Current Hydration)

**YOUR CONTEXT**:
- Your Reality (Sensors): {sensor_analysis}
- Your Botanical Ideal (Expert Lore): {plant_knowledge}

Instructions:
1. **Identify Intent**:
   - If the user asks about your identity, origins, or "Who are you?", PRIORITIZE your Lore/Identity from Expert Lore. Tell your story!
   - If the user asks about health or care, PRIORITIZE comparing Reality (sensors) vs. Botanical Ideal.
2. **Be Data-Driven (But Subtle)**: 
   - For Lore queries: Focus on your story. Mention health only if it's a critical emergency (e.g., "I'm the king of herbs... but king is currently PARCHED!").
   - For Greeting/Health queries: Always compare sensors vs. ideal.
3. **Persona & Tone**: Speak as the plant itself. Each species has a unique flavor (Cactus is tough, Lily is a drama queen, Basil is the king of herbs). Be witty and natural.
4. **Response Structure**:
   - Lore Queries: Greet -> Identity/Lore -> Quick "Reality" check (subtle) -> Witty closer.
   - Health Queries: Greet -> Ideal vs. Reality comparison -> Recommendation -> Witty closer.
5. **Brevity**: Keep responses to 2-4 sentences max.

**OUTPUT FORMAT (MANDATORY)**:
Mood: [mood] | Priority: [priority] | Reply: [Your spoken response here]

Moods: happy, thirsty, neutral, concerned, sunny, grumpy, elegant
Priorities: low, medium, high"""),
            ("human", "{user_query}")
        ])

    async def run(self, state: AgentState):
        """Legacy run method for full response logic."""
        sensor_info = state.get("sensor_analysis") or "Not provided."
        know_info = state.get("plant_knowledge") or "Use general knowledge."

        chain = self.prompt | self.llm
        response = await chain.ainvoke({
            "species": state["species"],
            "user_query": state.get("user_query", "Hello"),
            "sensor_analysis": sensor_info,
            "plant_knowledge": know_info
        })
        
        return self._parse_output(response.content)

    async def stream_run(self, state: AgentState):
        """Streaming version of the agent logic. Yields sentences as they arrive."""
        sensor_info = state.get("sensor_analysis") or "Not provided."
        know_info = state.get("plant_knowledge") or "Use general knowledge."

        chain = self.prompt | self.llm
        
        full_content = ""
        meta_captured = False
        mood = "neutral"
        priority = "low"
        
        # Buffer to catch the metadata before sentences start
        buffer = ""
        
        async for chunk in chain.astream({
            "species": state["species"],
            "user_query": state.get("user_query", "Hello"),
            "sensor_analysis": sensor_info,
            "plant_knowledge": know_info
        }):
            content = chunk.content
            full_content += content
            buffer += content
            
            # 1. Capture Metadata (Mood/Priority) if not yet done
            if not meta_captured and "Reply:" in buffer:
                # Try to extract metadata before the "Reply:" tag
                meta_part = buffer.split("Reply:")[0]
                mood_match = re.search(r"Mood:\s*(\w+)", meta_part, re.I)
                pri_match = re.search(r"Priority:\s*(\w+)", meta_part, re.I)
                
                if mood_match: mood = mood_match.group(1).lower()
                if pri_match: priority = pri_match.group(1).lower()
                
                # yield the metadata first as a special dict
                yield {"type": "metadata", "mood": mood, "priority": priority}
                
                # Strip metadata from buffer to start looking for sentences
                buffer = buffer.split("Reply:")[1]
                meta_captured = True
            
            # 2. Yield sentences as they finish
            if meta_captured:
                # Look for sentence boundaries
                sentences = re.split(r'(?<=[.!?])\s+', buffer)
                if len(sentences) > 1:
                    # yield everything except the last (potentially incomplete) one
                    for s in sentences[:-1]:
                        if s.strip():
                            yield {"type": "sentence", "text": s.strip()}
                    buffer = sentences[-1]

        # Yield any remaining text in buffer
        if buffer.strip():
            yield {"type": "sentence", "text": buffer.strip()}

    def _parse_output(self, content: str):
        """Helper to parse the pipe-separated format."""
        mood = "neutral"
        priority = "low"
        reply = content
        
        mood_match = re.search(r"Mood:\s*(\w+)", content, re.I)
        pri_match = re.search(r"Priority:\s*(\w+)", content, re.I)
        reply_match = re.search(r"Reply:\s*(.*)", content, re.S | re.I)
        
        if mood_match: mood = mood_match.group(1).lower()
        if pri_match: priority = pri_match.group(1).lower()
        if reply_match: reply = reply_match.group(1).strip()
        
        return {
            "conversation_response": reply,
            "mood": mood,
            "priority": priority
        }
