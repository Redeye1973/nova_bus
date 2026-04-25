---
created: 2026-04-25
type: reference
status: active
---

# Sessions Archive

## cursor_reports/
Auto-generated rapporten van Cursor sessies. Bestandsnaam format: `YYYY-MM-DD_topic_slug.md`

## claude_chats/
Handmatig geexporteerde chats van claude.ai.

### Claude.ai chat archiveren

1. Open Claude.ai chat
2. Klik export (rechterbovenhoek menu)
3. Save als `.md` file
4. Plaats in `docs/sessions/claude_chats/`
5. Bestandsnaam format: `YYYY-MM-DD_topic_slug.md`
6. Voeg frontmatter toe:
   ```
   ---
   created: 2026-04-25
   project: black_ledger
   type: claude_chat
   ---
   ```

Memory Curator pickt het automatisch op bij volgende reindex.
