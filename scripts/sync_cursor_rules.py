"""Sync .cursor/rules/ to backup archief."""
import shutil
from pathlib import Path
from datetime import datetime

REPO_RULES = Path(r"L:\!Nova V2\.cursor\rules")
ARCHIVE = Path(r"L:\! 2 Nova v2  OUTPUT !\Z RAPORT\Cursor\rules_backup")
DATE = datetime.now().strftime("%Y-%m-%d")

ARCHIVE.mkdir(parents=True, exist_ok=True)

for mdc_file in REPO_RULES.glob("*.mdc"):
    target = ARCHIVE / f"{DATE}_{mdc_file.name}"
    shutil.copy2(mdc_file, target)
    print(f"Synced: {target.name}")

current = ARCHIVE / "current"
current.mkdir(exist_ok=True)
for mdc_file in REPO_RULES.glob("*.mdc"):
    shutil.copy2(mdc_file, current / mdc_file.name)

print(f"Archive bijgewerkt: {ARCHIVE}")
