"""One-shot data migration: D&D class/rune layer for Aetherion (Grimm Reaper).

- progression.json: weapon_types + armor_weight per class
- shop_catalog.json: weapon_type on all weapons, weight on all armor,
  rune_sockets on tier>=3 gear, new "runes" category (10 runes)
- loot_tables.json: runes in loot_rare / loot_jackpot / dungeon_rare

Idempotent: re-running overwrites the same fields.
"""
from __future__ import annotations

import json
from pathlib import Path

DATA = Path(r"L:\! 2 Nova v2  OUTPUT !\Z Aetherion\blockout\aetherion_segment_01\data")

WEAPON_TYPES = {
    "short_sword": "sword", "iron_sword": "sword", "steel_blade": "sword",
    "flame_katana": "sword", "bronze_mace": "mace", "holy_mace": "mace",
    "runic_dagger": "dagger", "frost_spear": "spear", "dragon_lance": "spear",
    "war_axe": "axe", "ember_axe": "axe", "thunder_hammer": "hammer",
    "hunter_bow": "bow", "longbow": "bow", "storm_bow": "bow",
    "light_crossbow": "crossbow", "war_sling": "sling",
    "throwing_knives": "thrown", "arcane_focus": "focus",
    "poison_dart_pipe": "dart", "ancient_bolo": "bolo", "hunters_net": "net",
}

LIGHT_KEYS = ["cloth", "robe", "mage", "mystic", "arcane", "spellweave", "slipper", "frost", "padded"]
HEAVY_KEYS = ["iron", "bronze", "plate", "knight", "barbarian", "dragon", "chain", "greathelm"]
# everything else (leather, studded, scale, ranger, travel, swift, chaps, coif) -> medium

CLASS_PERMS = {
    "knight": {"weapon_types": ["sword", "axe", "spear", "bow"], "armor_weight": "heavy"},
    "guardian": {"weapon_types": ["mace", "hammer", "axe", "crossbow"], "armor_weight": "heavy"},
    "mage": {"weapon_types": ["staff", "focus", "dart"], "armor_weight": "light"},
    "cleric": {"weapon_types": ["mace", "hammer", "staff", "focus"], "armor_weight": "medium"},
}

RUNES = [
    {"id": "rune_of_might", "name": "Rune of Might", "price": 260, "slot": "rune",
     "atk": 2, "desc": "Socket: +2 ATK"},
    {"id": "rune_of_warding", "name": "Rune of Warding", "price": 260, "slot": "rune",
     "def": 2, "desc": "Socket: +2 DEF"},
    {"id": "rune_of_swiftness", "name": "Rune of Swiftness", "price": 300, "slot": "rune",
     "spd_bonus": 1, "desc": "Socket: +1 SPD"},
    {"id": "rune_of_vigor", "name": "Rune of Vigor", "price": 280, "slot": "rune",
     "hp_bonus": 6, "desc": "Socket: +6 max HP"},
    {"id": "rune_of_mind", "name": "Rune of Mind", "price": 280, "slot": "rune",
     "mp_bonus": 4, "desc": "Socket: +4 max MP"},
    {"id": "rune_of_flame", "name": "Rune of Flame", "price": 320, "slot": "rune",
     "atk": 1, "element": "fire", "desc": "Socket: +1 ATK, fire enchant"},
    {"id": "rune_of_frost", "name": "Rune of Frost", "price": 320, "slot": "rune",
     "atk": 1, "element": "ice", "desc": "Socket: +1 ATK, ice enchant"},
    {"id": "rune_of_storms", "name": "Rune of Storms", "price": 340, "slot": "rune",
     "atk": 1, "element": "lightning", "desc": "Socket: +1 ATK, lightning enchant"},
    {"id": "rune_of_shadows", "name": "Rune of Shadows", "price": 340, "slot": "rune",
     "atk": 1, "element": "dark", "desc": "Socket: +1 ATK, shadow enchant"},
    {"id": "rune_of_light", "name": "Rune of Light", "price": 340, "slot": "rune",
     "atk": 1, "element": "holy", "desc": "Socket: +1 ATK, holy enchant"},
]


def weapon_type(item: dict) -> str:
    iid = str(item.get("id", ""))
    if iid in WEAPON_TYPES:
        return WEAPON_TYPES[iid]
    for key, wt in [("crossbow", "crossbow"), ("bow", "bow"), ("sword", "sword"),
                    ("blade", "sword"), ("katana", "sword"), ("axe", "axe"),
                    ("mace", "mace"), ("hammer", "hammer"), ("dagger", "dagger"),
                    ("knives", "thrown"), ("spear", "spear"), ("lance", "spear"),
                    ("sling", "sling"), ("staff", "staff"), ("focus", "focus"),
                    ("wand", "focus"), ("dart", "dart"), ("bolo", "bolo"), ("net", "net")]:
        if key in iid:
            return wt
    return "sword"


def armor_weight(item: dict) -> str:
    iid = str(item.get("id", ""))
    for k in LIGHT_KEYS:
        if k in iid:
            return "light"
    for k in HEAVY_KEYS:
        if k in iid:
            return "heavy"
    return "medium"


def sockets_for_tier(tier: int) -> int:
    if tier >= 5:
        return 2
    if tier >= 3:
        return 1
    return 0


def main() -> None:
    # progression.json
    prog_path = DATA / "progression.json"
    prog = json.loads(prog_path.read_text(encoding="utf-8"))
    for cid, perms in CLASS_PERMS.items():
        if cid in prog.get("classes", {}):
            prog["classes"][cid].update(perms)
    prog_path.write_text(json.dumps(prog, indent=1, ensure_ascii=False), encoding="utf-8")

    # shop_catalog.json
    cat_path = DATA / "shop_catalog.json"
    cat = json.loads(cat_path.read_text(encoding="utf-8"))
    n_w = n_a = 0
    for group in ["weapons", "blacksmith"]:
        for item in cat.get(group, []):
            slot = str(item.get("slot", ""))
            if slot in ("weapon_melee", "weapon_ranged"):
                item["weapon_type"] = weapon_type(item)
                item["rune_sockets"] = sockets_for_tier(int(item.get("tier", 1)))
                n_w += 1
    for item in cat.get("armor", []):
        item["weight"] = armor_weight(item)
        item["rune_sockets"] = sockets_for_tier(int(item.get("tier", 1)))
        # Light armor is casters' gear: guarantee a small mana bonus from tier 2.
        if item["weight"] == "light" and int(item.get("tier", 1)) >= 2:
            item.setdefault("mp_bonus", max(1, int(item.get("tier", 1)) - 1))
        n_a += 1
    cat["runes"] = RUNES
    cat_path.write_text(json.dumps(cat, indent=1, ensure_ascii=False), encoding="utf-8")

    # loot_tables.json — runes as rare/jackpot drops
    loot_path = DATA / "loot_tables.json"
    loot = json.loads(loot_path.read_text(encoding="utf-8"))

    def ensure(table: str, entries: list[dict]) -> None:
        rows = loot.setdefault(table, [])
        have = {str(r.get("id")) for r in rows}
        for e in entries:
            if e["id"] not in have:
                rows.append(e)

    ensure("loot_rare", [
        {"id": "rune_stat_drop", "weight": 4, "item": "rune_of_warding"},
        {"id": "rune_might_drop", "weight": 4, "item": "rune_of_might"},
    ])
    ensure("dungeon_rare", [
        {"id": "rune_vigor_drop", "weight": 5, "item": "rune_of_vigor"},
        {"id": "rune_mind_drop", "weight": 4, "item": "rune_of_mind"},
    ])
    ensure("loot_jackpot", [
        {"id": "rune_flame_drop", "weight": 5, "item": "rune_of_flame"},
        {"id": "rune_frost_drop", "weight": 5, "item": "rune_of_frost"},
        {"id": "rune_storm_drop", "weight": 4, "item": "rune_of_storms"},
        {"id": "rune_shadow_drop", "weight": 3, "item": "rune_of_shadows"},
        {"id": "rune_light_drop", "weight": 3, "item": "rune_of_light"},
        {"id": "rune_swift_drop", "weight": 4, "item": "rune_of_swiftness"},
    ])
    loot_path.write_text(json.dumps(loot, indent=1, ensure_ascii=False), encoding="utf-8")

    print(f"tagged weapons={n_w} armor={n_a} runes={len(RUNES)}")
    print("classes:", {k: v for k, v in CLASS_PERMS.items()})


if __name__ == "__main__":
    main()
