# MCP Agent Workflow Improvements

## Summary

The MCP's main remaining friction is discovery and context retrieval, not Telegram connectivity. Prioritize tools that let an agent find conversations and messages quickly and read complete context with fewer repetitive calls.

## Key improvements

- Add `search_chats(query, limit)` for title, username, and participant-name discovery.
- Add `search_messages(query, chat_id?, sender_id?, from_date?, to_date?, limit, cursor?)`:
  - support both chat-scoped and global search;
  - return compact normalized messages;
  - include stable pagination cursors;
  - expose topic/thread metadata.
- Add `get_conversation_context(chat_id, message_id, before, after)` to return a message together with nearby messages, reply metadata, and topic/thread context.
- Add a higher-level history helper that automatically repeats TDLib history requests when it returns short pages while loading the local database.
- Add sender enrichment/caching so message results can include names without requiring repeated `get_user` calls.
- Improve compact message projections with useful media metadata, entities, reactions, views, forwarding origin, and reply counts while excluding file blobs.

## Live-update ergonomics

- Keep the existing subscription/poll/commit model.
- Add optional subscription filters for topic IDs and event kinds, defaulting to new messages and transcription results.
- Return explicit dropped-event information when the bounded buffer evicts old updates.
- Return a clear `has_more` indicator and preserve cursor behavior consistently on timeout.
- Add idempotency protection for repeated transcript requests and future write operations.

## Media follow-up

After discovery and context tools are in place, add:

- media/file metadata retrieval;
- thumbnail or downloaded-file access;
- explicit handling for unsupported media types;
- richer send operations such as reactions, edits, and replies if needed.

## Tests

Add coverage for:

- chat and global message search pagination;
- sender enrichment without duplicate lookups;
- context retrieval around a message and across reply/topic boundaries;
- short-page history recovery;
- topic-filtered subscriptions;
- buffer eviction reporting and cursor expiry;
- repeated search/transcription requests;
- TDLib errors and partially loaded local history.

## Assumptions

- The first implementation targets chat-scoped and global textual search.
- Results remain compact JSON and never expose TDLib's private SQLite schema.
- Search and context tools are read-only.
- Existing tool names and response fields remain backward compatible.
- The work should be split into small commits, beginning with discovery/search and context retrieval.
