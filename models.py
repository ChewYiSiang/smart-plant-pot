from datetime import datetime
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel, create_engine, Session

class Device(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    name: str
    species: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    readings: List["SensorReading"] = Relationship(back_populates="device")
    conversations: List["Conversation"] = Relationship(back_populates="device")

class SensorReading(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    device_id: str = Field(foreign_key="device.id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    temperature: float
    moisture: float
    light: float
    event: Optional[str] = None
    
    device: Device = Relationship(back_populates="readings")

class Conversation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    device_id: str = Field(foreign_key="device.id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    transcription: Optional[str] = None
    ai_response: Optional[str] = None
    mood: Optional[str] = None
    audio_file_path: Optional[str] = None
    
    device: Device = Relationship(back_populates="conversations")

class PlantKnowledge(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    species: str = Field(index=True)
    biological_info: str
    care_tips: str
    lore: str

# Database engine helper
from config import get_settings

def get_engine():
    settings = get_settings()
    return create_engine(settings.DATABASE_URL)

def init_db():
    SQLModel.metadata.create_all(get_engine())
