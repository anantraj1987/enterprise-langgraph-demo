# services/memory_service.py
 
from typing import List, Optional
from mem0 import Memory
from config.settings import settings
from utils.logger import logger

# Dedicated on-disk path so this app's local Qdrant store never collides with
# other processes/tools that use mem0's shared default of /tmp/qdrant.
LOCAL_VECTOR_STORE_PATH = str(settings.DATA_DIR / ".mem0_qdrant")


class Mem0Service:
    def __init__(self):
        self.memory: Optional[Memory] = None
        try:
            if settings.MEM0_API_KEY:
                self.memory = Memory.from_config({"api_key": settings.MEM0_API_KEY})
            else:
                self.memory = Memory.from_config(
                    {"vector_store": {"provider": "qdrant", "config": {"path": LOCAL_VECTOR_STORE_PATH}}}
                )
            logger.info("[MEM0] Memory Service initialized.")
        except Exception as e:
            logger.warning(f"[MEM0] Mem0 initialization notice ({str(e)}). Running in fallback mode.")
            try:
                self.memory = Memory.from_config(
                    {"vector_store": {"provider": "qdrant", "config": {"path": LOCAL_VECTOR_STORE_PATH, "on_disk": False}}}
                )
            except Exception as fallback_error:
                logger.error(f"[MEM0] Fallback initialization failed ({str(fallback_error)}). Memory disabled.")
                self.memory = None
 
    def get_user_memories(self, user_id: str) -> List[str]:
        if self.memory is None:
            return []
        try:
            results = self.memory.get_all(user_id=user_id)
            memories = []
            if isinstance(results, list):
                for item in results:
                    if isinstance(item, dict) and "memory" in item:
                        memories.append(item["memory"])
            elif isinstance(results, dict) and "results" in results:
                memories = [m.get("memory", "") for m in results.get("results", [])]
            return memories
        except Exception as e:
            logger.error(f"[MEM0] Failed to fetch memories: {str(e)}")
            return []
 
    def add_user_memory(self, user_id: str, interaction: str):
        if self.memory is None:
            return
        try:
            self.memory.add(interaction, user_id=user_id)
        except Exception as e:
            logger.error(f"[MEM0] Failed to save memory: {str(e)}")
 
    def close(self):
        """Safely close underlying vector store connections if present."""
        if self.memory is None:
            return
        try:
            if hasattr(self.memory, "vector_store") and hasattr(self.memory.vector_store, "client"):
                if hasattr(self.memory.vector_store.client, "close"):
                    self.memory.vector_store.client.close()
        except Exception:
            pass
 
 
mem0_service = Mem0Service()
