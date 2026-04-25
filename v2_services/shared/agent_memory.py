"""H08: Agent Memory — in-memory episodic + semantic storage with recall.

Usage in any agent:
    from shared.agent_memory import MemoryStore
    memory = MemoryStore(agent_id="agent_12")
    memory.store("completed bake job for 1234AB", tags=["bake", "success"])
    relevant = memory.recall("bake job")
"""
from __future__ import annotations

import time
import uuid
from collections import deque
from typing import Any, Deque, Dict, List, Optional


class MemoryStore:
    def __init__(self, agent_id: str, max_items: int = 1000):
        self.agent_id = agent_id
        self.max_items = max_items
        self.memories: Deque[Dict[str, Any]] = deque(maxlen=max_items)
        self.semantic_index: Dict[str, List[str]] = {}

    def store(
        self,
        content: str,
        tags: Optional[List[str]] = None,
        importance: float = 0.5,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        mem_id = str(uuid.uuid4())
        now = time.time()
        entry = {
            "id": mem_id,
            "agent_id": self.agent_id,
            "content": content,
            "tags": tags or [],
            "importance": importance,
            "context": context or {},
            "created_at": now,
            "access_count": 0,
            "last_accessed": now,
        }
        self.memories.append(entry)

        words = set(content.lower().split())
        for tag in (tags or []):
            words.add(tag.lower())
        for word in words:
            self.semantic_index.setdefault(word, []).append(mem_id)

        return mem_id

    def recall(
        self,
        query: str,
        limit: int = 5,
        tags: Optional[List[str]] = None,
        min_importance: float = 0.0,
    ) -> List[Dict[str, Any]]:
        query_words = set(query.lower().split())
        candidate_ids: Dict[str, int] = {}
        for word in query_words:
            for mem_id in self.semantic_index.get(word, []):
                candidate_ids[mem_id] = candidate_ids.get(mem_id, 0) + 1

        if tags:
            for tag in tags:
                for mem_id in self.semantic_index.get(tag.lower(), []):
                    candidate_ids[mem_id] = candidate_ids.get(mem_id, 0) + 2

        mem_by_id = {m["id"]: m for m in self.memories}
        scored = []
        for mem_id, word_hits in candidate_ids.items():
            mem = mem_by_id.get(mem_id)
            if not mem:
                continue
            if mem["importance"] < min_importance:
                continue
            recency = 1.0 / (1.0 + (time.time() - mem["created_at"]) / 3600)
            score = word_hits * 2.0 + mem["importance"] + recency * 0.5
            scored.append((score, mem))

        scored.sort(key=lambda x: -x[0])
        results = []
        for score, mem in scored[:limit]:
            mem["access_count"] += 1
            mem["last_accessed"] = time.time()
            results.append({**mem, "relevance_score": round(score, 3)})
        return results

    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        return list(self.memories)[-limit:]

    def summarize(self) -> Dict[str, Any]:
        all_tags: Dict[str, int] = {}
        for mem in self.memories:
            for tag in mem.get("tags", []):
                all_tags[tag] = all_tags.get(tag, 0) + 1
        return {
            "agent_id": self.agent_id,
            "total_memories": len(self.memories),
            "max_items": self.max_items,
            "index_words": len(self.semantic_index),
            "top_tags": dict(sorted(all_tags.items(), key=lambda x: -x[1])[:10]),
        }

    def forget(self, mem_id: str) -> bool:
        for i, mem in enumerate(self.memories):
            if mem["id"] == mem_id:
                del self.memories[i]
                return True
        return False
