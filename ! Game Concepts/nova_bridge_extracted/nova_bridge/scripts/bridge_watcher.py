#!/usr/bin/env python3
"""NOVA Bridge Watcher - monitors handoff directory for new tasks.

Draait continu in background, detecteert nieuwe opdracht files,
notificeert gebruiker (Windows toast), logt events.

Usage:
    python bridge_watcher.py              # Start watching
    python bridge_watcher.py --status     # Show current state
    python bridge_watcher.py --once       # Single check, geen loop
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Bridge root is parent of scripts/
BRIDGE_ROOT = Path(__file__).parent.parent
TO_CURSOR = BRIDGE_ROOT / "handoff" / "to_cursor"
FROM_CURSOR = BRIDGE_ROOT / "handoff" / "from_cursor"
SHARED_STATE = BRIDGE_ROOT / "handoff" / "shared_state"
ARCHIVE = BRIDGE_ROOT / "handoff" / "archive"
LOG_FILE = BRIDGE_ROOT / "bridge_watcher.log"
STATE_FILE = BRIDGE_ROOT / "bridge_state.json"


def log(msg, level="INFO"):
    """Write to log file + stdout."""
    ts = datetime.now().isoformat(timespec="seconds")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_state():
    """Load persistent state (seen files, last check time)."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception as e:
            log(f"State file corrupt, resetting: {e}", "WARN")
    return {
        "seen_opdrachten": [],
        "last_check": None,
        "total_processed": 0,
    }


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def windows_notify(title, body):
    """Try to show Windows toast notification. Silent fail if not available."""
    try:
        # Try using plyer if available
        from plyer import notification
        notification.notify(
            title=title,
            message=body,
            app_name="NOVA Bridge",
            timeout=10,
        )
        return True
    except ImportError:
        pass
    
    try:
        # Fallback: Windows 10+ via PowerShell
        import subprocess
        ps_cmd = f'''
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
        $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
        $template.GetElementsByTagName("text")[0].InnerText = "{title}"
        $template.GetElementsByTagName("text")[1].InnerText = "{body}"
        $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("NOVA Bridge").Show($toast)
        '''
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True, timeout=5
        )
        return True
    except Exception as e:
        log(f"Windows toast failed: {e}", "WARN")
        return False


def scan_opdrachten(state):
    """Find new opdracht files that have no corresponding response yet."""
    if not TO_CURSOR.exists():
        log(f"to_cursor directory niet gevonden: {TO_CURSOR}", "ERROR")
        return []
    
    opdrachten = sorted(TO_CURSOR.glob("*.md"))
    new_items = []
    
    for opd in opdrachten:
        # Check if already processed (response exists)
        response_name = opd.stem + "_response.md"
        response_path = FROM_CURSOR / response_name
        
        if response_path.exists():
            continue  # Already handled
        
        if opd.name in state["seen_opdrachten"]:
            continue  # Already notified, waiting for Cursor
        
        new_items.append(opd)
    
    return new_items


def process_new_opdrachten(new_items, state):
    """Handle new opdrachten: notify, log, update state."""
    for opd in new_items:
        log(f"Nieuwe opdracht gedetecteerd: {opd.name}")
        
        # Read first line for title
        try:
            first_line = opd.read_text(encoding="utf-8").split("\n")[0].lstrip("#").strip()
        except Exception:
            first_line = opd.stem
        
        # Notify
        notified = windows_notify(
            title="NOVA Bridge: Nieuwe opdracht",
            body=f"{first_line[:80]}\n\nCursor: lees {opd.name}"
        )
        if notified:
            log(f"Notified: {first_line}")
        
        # Mark seen
        state["seen_opdrachten"].append(opd.name)
    
    state["last_check"] = datetime.now().isoformat()
    save_state(state)


def cleanup_old_archives(max_days=30):
    """Move old processed files to archive."""
    if not ARCHIVE.exists():
        ARCHIVE.mkdir(parents=True, exist_ok=True)
    
    cutoff = datetime.now() - timedelta(days=max_days)
    archived = 0
    
    for folder in [TO_CURSOR, FROM_CURSOR]:
        for f in folder.glob("*.md"):
            try:
                mtime = datetime.fromtimestamp(f.stat().st_mtime)
                if mtime < cutoff:
                    # Check if has corresponding pair - only archive complete pairs
                    base = f.stem.replace("_response", "")
                    opd = TO_CURSOR / f"{base}.md"
                    resp = FROM_CURSOR / f"{base}_response.md"
                    if opd.exists() and resp.exists():
                        # Archive pair together
                        date_dir = ARCHIVE / mtime.strftime("%Y-%m")
                        date_dir.mkdir(exist_ok=True)
                        if opd.exists():
                            opd.rename(date_dir / opd.name)
                        if resp.exists():
                            resp.rename(date_dir / resp.name)
                        archived += 1
            except Exception as e:
                log(f"Archive error op {f.name}: {e}", "WARN")
    
    if archived > 0:
        log(f"Archived {archived} handoff pairs (>{max_days} dagen oud)")


def show_status():
    """Print current bridge state."""
    state = load_state()
    
    print("\n=== NOVA Bridge Status ===\n")
    print(f"Bridge root: {BRIDGE_ROOT}")
    print(f"Last check: {state.get('last_check', 'nooit')}")
    print(f"Total processed: {state.get('total_processed', 0)}")
    print()
    
    # Count files
    to_cursor_count = len(list(TO_CURSOR.glob("*.md"))) if TO_CURSOR.exists() else 0
    from_cursor_count = len(list(FROM_CURSOR.glob("*.md"))) if FROM_CURSOR.exists() else 0
    archive_count = sum(1 for _ in ARCHIVE.rglob("*.md")) if ARCHIVE.exists() else 0
    
    print(f"Opdrachten in to_cursor/: {to_cursor_count}")
    print(f"Responses in from_cursor/: {from_cursor_count}")
    print(f"Archive entries: {archive_count}")
    print()
    
    # Pending items
    if TO_CURSOR.exists():
        pending = []
        for opd in TO_CURSOR.glob("*.md"):
            resp_path = FROM_CURSOR / (opd.stem + "_response.md")
            if not resp_path.exists():
                pending.append(opd.name)
        
        if pending:
            print("Opdrachten wachtend op Cursor response:")
            for p in pending:
                print(f"  - {p}")
        else:
            print("Geen opdrachten wachtend. Alle handoffs compleet.")
    
    print()
    
    # Recent log entries
    if LOG_FILE.exists():
        lines = LOG_FILE.read_text(encoding="utf-8").strip().split("\n")
        if lines:
            print("Laatste 5 log entries:")
            for line in lines[-5:]:
                print(f"  {line}")


def watch_loop(interval=30):
    """Main loop: poll for new opdrachten."""
    log(f"Bridge watcher gestart. Poll interval: {interval}s")
    log(f"Watching: {TO_CURSOR}")
    
    state = load_state()
    cleanup_counter = 0
    
    try:
        while True:
            new_items = scan_opdrachten(state)
            if new_items:
                process_new_opdrachten(new_items, state)
            
            # Cleanup every ~hour
            cleanup_counter += interval
            if cleanup_counter >= 3600:
                cleanup_old_archives()
                cleanup_counter = 0
            
            time.sleep(interval)
    except KeyboardInterrupt:
        log("Watcher gestopt door gebruiker")
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="NOVA Bridge Watcher")
    parser.add_argument("--status", action="store_true", help="Toon huidige state")
    parser.add_argument("--once", action="store_true", help="Eén scan, geen loop")
    parser.add_argument("--interval", type=int, default=30, help="Poll interval in seconden")
    parser.add_argument("--cleanup", action="store_true", help="Archiveer oude handoffs")
    args = parser.parse_args()
    
    # Ensure directories exist
    for d in [TO_CURSOR, FROM_CURSOR, SHARED_STATE, ARCHIVE]:
        d.mkdir(parents=True, exist_ok=True)
    
    if args.status:
        show_status()
        return
    
    if args.cleanup:
        cleanup_old_archives()
        return
    
    if args.once:
        state = load_state()
        new_items = scan_opdrachten(state)
        if new_items:
            process_new_opdrachten(new_items, state)
            print(f"Processed {len(new_items)} nieuwe opdrachten")
        else:
            print("Geen nieuwe opdrachten")
        return
    
    watch_loop(interval=args.interval)


if __name__ == "__main__":
    main()
