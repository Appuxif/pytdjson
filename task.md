# Telegram message reactions through MCP

## Goal

Expose safe MCP operations for adding, removing, and inspecting reactions on Telegram messages. Support standard emoji and custom emoji reactions. Keep paid Star reactions and bot-only reaction APIs out of scope.

## MCP tools

Add write-annotated tools:

- `add_message_reaction(chat_id, message_id, reaction_type, value, is_big=False, update_recent_reactions=False)`;
- `remove_message_reaction(chat_id, message_id, reaction_type, value)`.

The target `chat_id` must be present in `PYTDJSON_ALLOW_SEND_TO_CHATS`, using the same fail-closed policy as `send_message` and `forward_messages`. Accept only `reaction_type="emoji"` and `reaction_type="custom_emoji"`. Reject paid reactions and unknown types with clear validation errors. Return a compact result containing the operation, target IDs, reaction type, and value.

Add read-only tools:

- `get_message_available_reactions(chat_id, message_id, row_size=25)`;
- `get_message_added_reactions(chat_id, message_id, reaction_type=None, value=None, offset="", limit=100)`.

Project available and added reactions into stable compact JSON, including reaction type, emoji/custom ID, counts, sender information, pagination offset, and completion status where provided by TDLib.

## API and runtime integration

- Reuse the existing low-level `add_message_reaction`, `remove_message_reaction`, and `get_message_available_reactions` wrappers.
- Add runtime methods that delegate reaction operations consistently with the existing send and read methods.
- Correct `get_message_added_reactions` pagination to use TDLib's string offset while preserving the existing API where practical.
- Do not add outgoing-message suppression: reactions update interaction state and do not create messages.
- Keep the existing message projection's reaction summaries compatible.
- Allow reaction-related updates to be selected through existing subscription event-type filters without adding them to the default message-only subscription.

## Validation and errors

- Validate positive chat and message IDs through the MCP schema.
- Validate emoji reaction values as non-empty strings and custom emoji values as valid numeric IDs.
- Reject unsupported paid reactions before contacting TDLib.
- Preserve and surface TDLib errors, including unavailable reactions, permission restrictions, protected messages, and messages that no longer exist.
- Read-only reaction inspection must not require the send allowlist.

## Tests and documentation

- Test exact TDLib request construction for emoji and custom emoji add/remove operations.
- Test optional `is_big` and `update_recent_reactions` flags.
- Test available and added reaction projections, including pagination offsets and limits.
- Test rejection of paid/unknown reaction types, empty values, malformed custom emoji IDs, and invalid limits.
- Test target-chat allowlist enforcement for add and remove operations.
- Test that read tools work without send permission.
- Test that reaction update types can be selected through subscriptions without changing default subscription behavior.
- Document the new tools, allowlist requirement, supported reaction types, and excluded paid reactions in the MCP README.
- Run the full test suite, formatting checks, and `git diff --check`.

## Scope boundaries

- Do not implement paid Star reactions in this change.
- Do not expose bot-only `setMessageReactions`.
- Do not access TDLib's private SQLite database directly.
- Do not change default live-update filtering from new messages and transcription results.
