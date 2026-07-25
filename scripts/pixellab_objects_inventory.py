"""One-off: full PixelLab Objects page inventory + usability assessment dump.

Pages list_objects for every status and writes a categorized JSON summary to
L:\\! 2 Nova v2 OUTPUT !\\Z RAPORT\\pixellab_objects_inventory.json
"""
from __future__ import annotations

import json
import re
import ssl
import time

# Same workaround as sync_pixellab_all_assets.py (local CA chain issue).
ssl._create_default_https_context = ssl._create_unverified_context
from collections import Counter
from pathlib import Path
from urllib.request import Request, urlopen

MCP = "https://api.pixellab.ai/mcp"
KEY_PATHS = [
    Path(r"L:\ZZZZZZ ZZ PROMPTS\Project Aetherion\Secret pixellab ai key\key.txt"),
    Path(r"L:\Nova\Key's\PixelLab.txt"),
]
OUT_JSON = Path(r"L:\!Nova V2\! 2 Nova v2 OUTPUT !\Z RAPORT\pixellab_objects_inventory.json")

# Format: "  <uuid> | <name (truncated)> | <meta>"
LINE_RE = re.compile(r"^\s*([0-9a-f-]{36})\s*\|\s*(.*?)\s*(?:\|\s*(.*))?$", re.I)

CATEGORY_RULES = [
    ("weapons", re.compile(r"sword|blade|katana|axe|mace|hammer|dagger|spear|lance|bow|crossbow|sling|net|bolo|halberd|scythe|trident|whip|flail|wand|staff", re.I)),
    ("jewelry", re.compile(r"ring|amulet|pendant|locket|medallion|torc|gem|jewel", re.I)),
    ("potions", re.compile(r"potion|elixir|tonic|flask|vial|antidote|ether", re.I)),
    ("runes", re.compile(r"\brune\b|rune stone|runestone", re.I)),
    ("icons", re.compile(r"icon|spell |key |torch", re.I)),
    ("buildings", re.compile(r"house|building|roof|wall|gate|tower|kit|shop|inn|temple|church|castle", re.I)),
    ("tiles", re.compile(r"tile|tileset|floor|path|cobble|wang|terrain", re.I)),
    ("bestiary", re.compile(r"goblin|orc|skeleton|slime|wolf|spider|dragon|troll|imp|zombie|ghoul|mimic|kobold|bandit|rat|bear|harpy|wight|golem|ogre|wyvern|basilisk|ettin|behir|gnoll|bugbear|owlbear|cube|siren|fallen", re.I)),
    ("characters", re.compile(r"hero|knight|mage|cleric|guardian|npc|villager|merchant|character|portrait", re.I)),
    ("landmarks", re.compile(r"ruin|obelisk|statue|monolith|shrine|landmark|dolmen|menhir", re.I)),
    ("nature", re.compile(r"tree|bush|cactus|rock|flower|grass|plant", re.I)),
    ("fx", re.compile(r"fx|effect|explosion|slash|impact|d20|dice", re.I)),
    ("ui", re.compile(r"\bui\b|panel|button|frame|cursor|bar\b", re.I)),
    ("sea", re.compile(r"sea|fish|shark|kraken|eel|whale|jelly|crab|boat|ship", re.I)),
    ("vehicles", re.compile(r"motorcycle|car |vehicle|oldsmobile|royale", re.I)),
    ("excluded_ninja", re.compile(r"ninja|shinobi|shuriken|kunai", re.I)),
]


def load_key() -> str:
    for p in KEY_PATHS:
        if p.exists():
            return p.read_text(encoding="utf-8").strip()
    raise SystemExit("no pixellab key")


def mcp_call(key: str, name: str, arguments: dict) -> str:
    body = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    }).encode()
    req = Request(MCP, data=body, method="POST", headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    })
    with urlopen(req, timeout=120) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    data_line = None
    for line in raw.splitlines():
        if line.startswith("data:"):
            data_line = line[5:].strip()
    payload = json.loads(data_line or raw.strip())
    if "error" in payload:
        raise RuntimeError(payload["error"])
    content = payload.get("result", {}).get("content", [])
    return "\n".join(c.get("text", "") for c in content if c.get("type") == "text")


def categorize(name: str, meta: str) -> str:
    blob = f"{name} {meta}"
    for folder, pattern in CATEGORY_RULES:
        if pattern.search(blob):
            return folder
    return "other"


def list_status(key: str, status: str) -> list[dict]:
    out: list[dict] = []
    offset = 0
    while True:
        text = mcp_call(key, "list_objects", {
            "limit": 50, "offset": offset, "status_filter": status,
        })
        page = 0
        for line in text.splitlines():
            m = LINE_RE.match(line)
            if not m:
                continue
            oid, name, meta = m.group(1), m.group(2).strip(), (m.group(3) or "").strip()
            out.append({"id": oid, "name": name, "meta": meta, "status": status})
            page += 1
        offset += 50
        if page == 0:
            break
        time.sleep(0.05)
    return out


def main() -> None:
    key = load_key()
    all_objects: list[dict] = []
    for status in ["completed", "review", "pending", "processing", "failed"]:
        objs = list_status(key, status)
        print(f"{status}: {len(objs)}")
        all_objects.extend(objs)
    cats: Counter = Counter()
    for o in all_objects:
        o["category"] = categorize(o["name"], o["meta"])
        cats[o["category"]] += 1
    summary = {
        "total": len(all_objects),
        "by_status": dict(Counter(o["status"] for o in all_objects)),
        "by_category": dict(cats.most_common()),
        "objects": all_objects,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    print("category breakdown:")
    for k, v in cats.most_common():
        print(f"  {v:5d}  {k}")
    print(f"written: {OUT_JSON}")


if __name__ == "__main__":
    main()
