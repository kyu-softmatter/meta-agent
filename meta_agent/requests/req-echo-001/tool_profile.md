# tool_profile tp-echo-001

Tool `echo` (analysis_software), read from meta_agent/tests/fixtures/echo/README.md. Analysis permission: none; binaries and runtime were not analysed.

## Claims

- **observed** (documentation): echo reads one JSON object from standard input and writes one JSON object to standard output; at ## Command
- **observed** (documentation): the exit status is zero whether echo answers or reports an error; the error is in the output; at ## Command
- **observed** (documentation): the input is an object with one required string field, message, which must not be empty; at ## Input
- **observed** (documentation): the output carries message, the same text, and length, the number of characters in message; at ## Output
- **observed** (documentation): a missing, non-string or empty message returns the error ECHO-INPUT-001 of category invalid_input, not retryable; at ## Errors
- **derived** (documentation): length equals the character count of message, so it can be checked against an independent count of the same text; at ## Output
- **observed** (documentation): echo has no state and no side effects; at (preamble)
- **unknown** (documentation): a maximum message length exists; at no locus; requires: a statement in the documentation, or a run in a sandbox with growing messages

## Gaps

- a maximum message length exists (no_material); requires: a statement in the documentation, or a run in a sandbox with growing messages
- the real echo binary behaves as the mock adapter does (permission_required); requires: analysis_permission confirmed by a person (granted_by, scope, basis, date)

Parameter candidates: `message`.
