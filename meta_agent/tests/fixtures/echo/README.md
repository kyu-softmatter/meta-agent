# echo — a tool that returns what it is given

`echo` is a command-line tool used as the first, harmless target of the Agent Designer. It has no backend, no state and no side effects.

## Command

```
echo
```

The command reads one JSON object from standard input and writes one JSON object to standard output. It exits with status 0 whether it answers or reports an error; the error is in the output.

## Input

A JSON object with one required field:

| field | type | meaning |
|---|---|---|
| `message` | string | the text to echo back; must not be empty |

## Output

A JSON object:

| field | type | meaning |
|---|---|---|
| `message` | string | the same text |
| `length` | integer | the number of characters in `message` |

## Errors

One error is defined. It follows the error contract of `contracts/schemas/error_contract.schema.json`.

| code | category | when | retryable |
|---|---|---|---|
| `ECHO-INPUT-001` | `invalid_input` | `message` is missing, not a string, or empty | no |

## Limits

The documentation does not state a maximum message length.
