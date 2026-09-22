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

## Message forwarding through MCP

### Goal

Add a safe `forward_messages` tool that lets an agent forward or copy messages between Telegram chats while preserving message order, supporting forum topics, enforcing the existing send allowlist, and reporting per-message failures.

### API and TDLib integration

- Extend the existing `API.forward_messages` wrapper with `forum_topic_id`.
- Encode a forum destination as TDLib's `messageTopicForum`.
- Keep the existing wrapper signature compatible for callers that already pass `message_thread_id`, but stop silently ignoring it; return a clear error because ordinary message threads are not supported by TDLib's `forwardMessages` request.
- Preserve support for TDLib's `send_copy` and `remove_caption` flags.
- Keep TDLib's returned message order and nullable entries so protected or otherwise unforwardable messages can be identified.
- Validate that the batch contains 1–100 message IDs in strictly increasing order before making the TDLib request.

### MCP tool

Add a write-annotated `forward_messages` tool with:

- `from_chat_id`: source chat;
- `message_ids`: 1–100 strictly increasing source message IDs;
- `to_chat_id`: destination chat;
- required `send_copy`: explicit choice between forwarding and copying;
- optional `forum_topic_id`: forum topic in the destination;
- optional `remove_caption`.

Only the destination chat must be present in `PYTDJSON_ALLOW_SEND_TO_CHATS` (or be covered by `*`), matching `send_message` policy. Reject the request before contacting Telegram when the destination is not allowed, the batch is invalid, or conflicting thread parameters are supplied.

Return a compact result containing the source and destination IDs, the requested message IDs, the projected forwarded messages in source order, `failed_message_ids`, and forwarded/failed counts. A `null` projected message is retained at its original position when TDLib reports a per-message failure.

### Update-buffer behavior

Remember every successfully created destination message as an outgoing message in the runtime's existing ignored-message state. This prevents the agent's own forwarded messages from being treated as incoming work by `poll_updates`, including partial-success batches, and keeps the behavior consistent with `send_message`.

### Documentation and tests

- Document the new tool, the destination allowlist, the explicit `send_copy` requirement, the 100-message limit, forum-topic support, and partial-failure behavior in the MCP README.
- Test exact TDLib request construction with and without a forum topic.
- Test rejection of unsupported legacy message-thread forwarding and invalid/non-increasing batches.
- Test destination allowlist enforcement and the required `send_copy` parameter at the MCP layer.
- Test forwarding with partial TDLib results and verify that all successful destination IDs are added to the ignored outgoing-message state.
- Run the full unit-test suite, formatting checks, and `git diff --check`.

### Scope boundaries

- Do not inspect or modify TDLib's SQLite database directly.
- Do not add preflight history requests; TDLib remains the source of truth for whether each message can be forwarded or copied.
- Do not add multi-agent routing or source-chat permissions beyond the existing destination send policy.
- Do not commit or push until the implementation and tests have been reviewed.
