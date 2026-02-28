import asyncio
import os
import sys

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.conversation_agent import ConversationAgent

async def verify_jokes():
    agent = ConversationAgent()
    species_list = ["Cactus", "Basil", "Lily", "Aloe Vera"]
    
    print("\n--- Verifying Species-Specific Jokes ---\n")
    
    for species in species_list:
        print(f"Testing joke for: {species}")
        state = {
            "device_id": "test_id",
            "species": species,
            "user_query": "Tell me a joke!",
            "sensor_analysis": "Temp: 25C, Moisture: 50%, Light: 80%",
            "plant_knowledge": f"Expert info about {species}."
        }
        
        try:
            result = await agent.run(state)
            print(f"Mood: {result['mood']}")
            print(f"Reply: {result['conversation_response']}")
        except Exception as e:
            print(f"Error testing {species}: {e}")
        print("-" * 40)

if __name__ == "__main__":
    asyncio.run(verify_jokes())
