from typing import TypedDict, List, Optional, Annotated
import operator

class AgentState(TypedDict):
    # Input Data
    device_id: str
    user_query: Optional[str]
    sensor_data: dict # latest readings
    
    # intermediate results
    sensor_analysis: Optional[str]
    plant_knowledge: Optional[str]
    conversation_response: Optional[str]
    
    # Final Output
    reply_text: str
    mood: str
    icons: List[str]
    priority: str
    audio_path: Optional[str]
