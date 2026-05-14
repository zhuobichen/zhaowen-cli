# winotes-cli

AI-friendly command-line interface for Windows Sticky Notes, powered by [winotes](https://github.com/JeanTheMan/winotes).

## Installation

```
pip install winotes-cli
```

## Usage

All commands output JSON by default — ideal for AI agents and scripts.

```
wn <command> [options]
```

### Commands

| Command | Description |
|---|---|
| `wn list` | List all active notes |
| `wn list -q <text>` | Filter notes by content |
| `wn get <id>` | Get a single note by ID |
| `wn create -t "text"` | Create a new note |
| `wn create -t "hello" --theme Blue --on-top` | Create with options |
| `wn create -f note.txt` | Create from file |
| `wn update <id> -t "new text"` | Update note content |
| `wn update <id> --theme Green` | Change note color |
| `wn update <id> --open true` | Set open/closed state |
| `wn delete <id>` | Soft-delete (recoverable) |
| `wn delete <id> --permanent` | Hard-delete |
| `wn restore <id>` | Restore a soft-deleted note |
| `wn search <query>` | Search notes by text |
| `wn themes` | List valid theme names |

### Options

| Flag | Scope | Description |
|---|---|---|
| `--pretty` | list/get/search | Pretty-print JSON output |
| `-n <N>` | list/search | Limit results to N notes |
| `-c` | list/search | Case-sensitive search |
| `-a` | list | Include soft-deleted notes |
| `--theme <T>` | create/update | Set note color theme |
| `--minimized` | create | Create note minimized |
| `--on-top` | create/update | Pin note always on top |
| `--open <bool>` | update | Set window open state (true/false) |

### Examples

```bash
# AI agent reads current notes
wn list -n 5

# Find notes about a topic
wn search "CMAQ" --pretty

# Create a reminder
wn create -t "Check deploy at 3pm" --theme Yellow --on-top

# Update a note
wn update aeefb726-fc45-4368-9ecc-296033986c45 -t "Updated content"

# Read a note by ID for piping
wn get aeefb726-fc45-4368-9ecc-296033986c45 | jq .text_plain
```

## Requirements

- Windows 10 / 11 with Sticky Notes installed
- Python 3.10+
