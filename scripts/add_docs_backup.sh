#!/bin/bash
cp /root/nova-backup.sh /root/nova-backup.sh.bak

python3 << 'PYTHON'
with open("/root/nova-backup.sh") as f:
    content = f.read()

docs_block = """
# Docs sync
echo "-- Docs sync"
if [ -d /docker/nova-v2/docs ]; then
  mkdir -p "$STAGING/docs-$(date +%Y%m%d_%H%M%S)"
  cp -r /docker/nova-v2/docs "$STAGING/docs-$(date +%Y%m%d_%H%M%S)/" 2>/dev/null || true
  echo "  Docs synced: $(find /docker/nova-v2/docs -type f | wc -l) files"
else
  echo "  WARN: docs directory not found"
fi

"""

if "Docs sync" not in content:
    borg_pos = content.find("borg create")
    if borg_pos > 0:
        last_nl = content.rfind('\n', 0, borg_pos)
        content = content[:last_nl+1] + docs_block + content[last_nl+1:]
    else:
        content += '\n' + docs_block
    with open("/root/nova-backup.sh", "w") as f:
        f.write(content)
    print("Updated nova-backup.sh with docs sync step")
else:
    print("Docs sync already present, skipping")
PYTHON

bash -n /root/nova-backup.sh && echo "Syntax: OK" || echo "SYNTAX ERROR"
