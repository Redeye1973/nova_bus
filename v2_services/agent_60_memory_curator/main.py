"""NOVA Memory Curator — centralized project memory with file access and full-text search."""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import os

app = FastAPI(title="NOVA Memory Curator", version="1.0")

DOCS_ROOT = Path(os.getenv("DOCS_ROOT", "/docs"))


class WriteRequest(BaseModel):
    path: str
    content: str
    overwrite: bool = False


class AppendRequest(BaseModel):
    path: str
    content: str


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {"status": "ok", "docs_accessible": DOCS_ROOT.exists()}


@app.get("/memory/list")
async def list_memory(path: str = Query(default="")) -> Dict[str, Any]:
    target = DOCS_ROOT / path
    if not target.exists():
        raise HTTPException(404, f"Path not found: {path}")

    items = []
    for item in sorted(target.iterdir()):
        items.append({
            "name": item.name,
            "type": "directory" if item.is_dir() else "file",
            "size": item.stat().st_size if item.is_file() else None,
            "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
        })
    return {"path": path, "items": items}


@app.get("/memory/get")
async def get_memory(path: str) -> Dict[str, Any]:
    target = DOCS_ROOT / path
    if not target.exists() or not target.is_file():
        raise HTTPException(404, f"File not found: {path}")

    return {
        "path": path,
        "content": target.read_text(encoding="utf-8"),
        "modified": datetime.fromtimestamp(target.stat().st_mtime).isoformat(),
    }


@app.post("/memory/write")
async def write_memory(body: WriteRequest) -> Dict[str, Any]:
    target = DOCS_ROOT / body.path
    if target.exists() and not body.overwrite:
        raise HTTPException(409, "File exists, use overwrite=true")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body.content, encoding="utf-8")
    return {"path": body.path, "written": True}


@app.post("/memory/append")
async def append_memory(body: AppendRequest) -> Dict[str, Any]:
    target = DOCS_ROOT / body.path
    target.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().isoformat()
    with open(target, "a", encoding="utf-8") as f:
        f.write(f"\n\n## {timestamp}\n\n{body.content}\n")

    return {"path": body.path, "appended": True, "timestamp": timestamp}


@app.get("/memory/search")
async def search_memory(q: str, project: Optional[str] = None) -> Dict[str, Any]:
    results: List[Dict[str, Any]] = []
    search_root = DOCS_ROOT / "projects" / project if project else DOCS_ROOT

    if not search_root.exists():
        return {"query": q, "project_filter": project, "results": [], "count": 0}

    for md_file in search_root.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            if q.lower() in content.lower():
                for i, line in enumerate(content.split("\n")):
                    if q.lower() in line.lower():
                        results.append({
                            "path": str(md_file.relative_to(DOCS_ROOT)),
                            "line": i + 1,
                            "snippet": line.strip()[:200],
                        })
                        break
        except Exception:
            continue

    return {"query": q, "project_filter": project, "results": results, "count": len(results)}


@app.get("/memory/timeline")
async def get_timeline(project: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
    events: List[Dict[str, Any]] = []

    if project:
        log_path = DOCS_ROOT / "projects" / project / "progress" / "daily_log.md"
        if log_path.exists():
            content = log_path.read_text(encoding="utf-8")
            for line in content.split("\n"):
                if line.startswith("## 20"):
                    events.append({
                        "type": "daily_log",
                        "date": line.replace("## ", "").strip(),
                        "project": project,
                    })

    sessions_dir = DOCS_ROOT / "sessions" / "cursor_reports"
    if sessions_dir.exists():
        for session_file in sessions_dir.glob("*.md"):
            mtime = datetime.fromtimestamp(session_file.stat().st_mtime)
            events.append({
                "type": "cursor_session",
                "date": mtime.isoformat(),
                "name": session_file.stem,
            })

    events.sort(key=lambda e: e["date"], reverse=True)
    return {"events": events[:50], "count": len(events)}


@app.post("/invoke")
async def invoke(body: Dict[str, Any]) -> Dict[str, Any]:
    action = body.get("action", "")
    if action == "list":
        return await list_memory(body.get("path", ""))
    elif action == "get":
        return await get_memory(body["path"])
    elif action == "search":
        return await search_memory(body["query"], body.get("project"))
    elif action == "timeline":
        return await get_timeline(body.get("project"), body.get("days", 30))
    elif action == "write":
        return await write_memory(WriteRequest(**body))
    elif action == "append":
        return await append_memory(AppendRequest(**body))
    else:
        raise HTTPException(400, f"Unknown action: {action}")
