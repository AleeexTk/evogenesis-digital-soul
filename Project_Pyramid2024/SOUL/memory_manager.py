import json
import os
import time
from datetime import datetime

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "memory_core.json")

class MemoryManager:
    def __init__(self):
        self.memory = self._load_memory()

    def _load_memory(self):
        if not os.path.exists(MEMORY_FILE):
            return self._init_memory()
        try:
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[SOUL] Memory corruption detected: {e}")
            return self._init_memory()

    def _init_memory(self):
        return {
            "meta": {"version": "1.0", "last_sync": datetime.now().isoformat()},
            "short_term": {"recent_events": []},
            "long_term": {"principles": [], "learned_facts": {}},
            "associative": {"nodes": [], "links": []}
        }

    def _save_memory(self):
        self.memory["meta"]["last_sync"] = datetime.now().isoformat()
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.memory, f, indent=2, ensure_ascii=False)

    def memorize(self, key, value, memory_type="short_term"):
        """Stores a piece of information."""
        if memory_type == "short_term":
            event = {
                "timestamp": datetime.now().isoformat(),
                "key": key,
                "value": value
            }
            self.memory["short_term"]["recent_events"].append(event)
            # Keep short term limit? (e.g. last 50 events)
            if len(self.memory["short_term"]["recent_events"]) > 50:
                self.memory["short_term"]["recent_events"].pop(0)
                
        elif memory_type == "long_term":
            self.memory["long_term"]["learned_facts"][key] = value
            
        self._save_memory()
        return True

    def recall(self, query, memory_type="all"):
        """Retrieves information based on a key."""
        results = {}
        
        if memory_type == "all" or memory_type == "long_term":
             if query in self.memory["long_term"]["learned_facts"]:
                 results["long_term"] = self.memory["long_term"]["learned_facts"][query]
        
        if memory_type == "all" or memory_type == "short_term":
            # Simple keyword search in recent events
            matches = [e for e in self.memory["short_term"]["recent_events"] if query in str(e)]
            if matches:
                 results["short_term"] = matches

        return results

    def get_full_memory(self):
        return self.memory

# Singleton instance
soul_memory = MemoryManager()
