import asyncio
from typing import Dict, Optional

class StreamingManager:
    """
    Manages asynchronous queues for real-time audio streaming.
    Bridges the Ingest process (AI thinking) and the /stream endpoint (Speaking).
    """
    def __init__(self):
        # Maps convo_id -> asyncio.Queue[Dict]
        self.queues: Dict[str, asyncio.Queue] = {}
        # Maps convo_id -> asyncio.Event (Finished signal)
        self.done_events: Dict[str, asyncio.Event] = {}

    def start_stream(self, convo_id: str):
        """Initializes queues for a new conversation."""
        self.queues[convo_id] = asyncio.Queue()
        self.done_events[convo_id] = asyncio.Event()

    async def put(self, convo_id: str, item: dict):
        """Pushes a metadata or sentence object into the queue."""
        if convo_id in self.queues:
            await self.queues[convo_id].put(item)

    async def get(self, convo_id: str) -> Optional[dict]:
        """Pulls the next available chunk for streaming."""
        if convo_id not in self.queues:
            return None
            
        queue = self.queues[convo_id]
        done_event = self.done_events[convo_id]
        
        while True:
            try:
                # Wait for an item with a timeout to check for done status
                return await asyncio.wait_for(queue.get(), timeout=0.1)
            except asyncio.TimeoutError:
                if done_event.is_set() and queue.empty():
                    return None
                continue

    def finish_stream(self, convo_id: str):
        """Signals that no more data will be sent for this conversation."""
        if convo_id in self.done_events:
            self.done_events[convo_id].set()

    def cleanup(self, convo_id: str):
        """Removes the conversation state from memory."""
        self.queues.pop(convo_id, None)
        self.done_events.pop(convo_id, None)

# Global singleton instance
streaming_manager = StreamingManager()
