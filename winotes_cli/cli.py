"""winotes-cli — AI-friendly CLI for Windows Sticky Notes."""

import argparse
import json
import sys
from datetime import datetime
from typing import Optional

from winotes import Winotes

THEMES = {"Yellow", "Blue", "Green", "Pink", "Purple", "Gray", "Charcoal"}


def _format_note(note: dict) -> dict:
    """Convert datetime fields to ISO strings for JSON serialization."""
    out = dict(note)
    for key in ("created_at", "updated_at", "deleted_at"):
        val = out.get(key)
        if isinstance(val, datetime):
            out[key] = val.isoformat()
    out["is_open"] = bool(out.get("is_open"))
    out["is_always_on_top"] = bool(out.get("is_always_on_top"))
    return out


def _output(notes, pretty: bool = False):
    """Print notes as JSON to stdout."""
    if isinstance(notes, list):
        data = [_format_note(n) for n in notes]
    elif isinstance(notes, dict):
        data = _format_note(notes)
    else:
        data = notes
    indent = 2 if pretty else None
    print(json.dumps(data, ensure_ascii=False, indent=indent))


def _die(msg: str, code: int = 1):
    print(json.dumps({"error": msg}), file=sys.stderr)
    sys.exit(code)


def cmd_list(args):
    sn = Winotes()
    notes = sn.list_notes(include_deleted=args.all)
    if args.query:
        notes = sn.search_notes(args.query, case_sensitive=args.case_sensitive)
    if args.limit and len(notes) > args.limit:
        notes = notes[:args.limit]
    _output(notes, pretty=args.pretty)


def cmd_get(args):
    sn = Winotes()
    note = sn.get_note(args.id)
    if note is None:
        _die(f"Note not found: {args.id}")
    _output(note, pretty=args.pretty)


def cmd_create(args):
    sn = Winotes()
    text = args.text
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()
    if not text:
        _die("Text is required (use --text or --file)")
    note = sn.create_note(
        text=text,
        theme=args.theme,
        is_open=not args.minimized,
        is_always_on_top=args.on_top,
    )
    _output(note, pretty=args.pretty)


def cmd_update(args):
    sn = Winotes()
    text = args.text
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()
    kwargs = {}
    if text is not None:
        kwargs["text"] = text
    if args.theme is not None:
        kwargs["theme"] = args.theme
    if args.open is not None:
        kwargs["is_open"] = args.open
    if args.on_top is not None:
        kwargs["is_always_on_top"] = args.on_top
    if not kwargs:
        _die("Nothing to update (use --text, --theme, --open, --on-top)")
    note = sn.update_note(args.id, **kwargs)
    if note is None:
        _die(f"Note not found: {args.id}")
    _output(note, pretty=args.pretty)


def cmd_delete(args):
    sn = Winotes()
    ok = sn.delete_note(args.id, soft=not args.permanent)
    if not ok:
        _die(f"Note not found: {args.id}")
    _output({"deleted": args.id, "permanent": args.permanent})


def cmd_restore(args):
    sn = Winotes()
    note = sn.restore_note(args.id)
    if note is None:
        _die(f"Note not found or not deleted: {args.id}")
    _output(note, pretty=args.pretty)


def cmd_search(args):
    sn = Winotes()
    results = sn.search_notes(args.query, case_sensitive=args.case_sensitive)
    if args.limit and len(results) > args.limit:
        results = results[:args.limit]
    _output(results, pretty=args.pretty)


def cmd_themes(_args):
    print(json.dumps(sorted(THEMES)))


def main():
    parser = argparse.ArgumentParser(
        prog="wn",
        description="AI-friendly CLI for Windows Sticky Notes",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # list
    p_list = sub.add_parser("list", help="List all notes")
    p_list.add_argument("-a", "--all", action="store_true", help="Include deleted notes")
    p_list.add_argument("-q", "--query", help="Filter by text content")
    p_list.add_argument("-c", "--case-sensitive", action="store_true")
    p_list.add_argument("-n", "--limit", type=int, help="Max results")
    p_list.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    p_list.set_defaults(func=cmd_list)

    # get
    p_get = sub.add_parser("get", help="Get a single note by ID")
    p_get.add_argument("id", help="Note UUID")
    p_get.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    p_get.set_defaults(func=cmd_get)

    # create
    p_create = sub.add_parser("create", help="Create a new note")
    p_create.add_argument("-t", "--text", help="Note content")
    p_create.add_argument("-f", "--file", help="Read content from file")
    p_create.add_argument("--theme", default="Yellow", choices=sorted(THEMES))
    p_create.add_argument("--minimized", action="store_true", help="Create minimized")
    p_create.add_argument("--on-top", action="store_true", help="Pin on top")
    p_create.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    p_create.set_defaults(func=cmd_create)

    # update
    p_update = sub.add_parser("update", help="Update an existing note")
    p_update.add_argument("id", help="Note UUID")
    p_update.add_argument("-t", "--text", help="New text content")
    p_update.add_argument("-f", "--file", help="Read new content from file")
    p_update.add_argument("--theme", choices=sorted(THEMES), help="Change theme")
    p_update.add_argument("--open", action=argparse.BooleanOptionalAction, default=None, help="Set open state (use --no-open to unset)")
    p_update.add_argument("--on-top", action=argparse.BooleanOptionalAction, default=None, help="Set always-on-top (use --no-on-top to unset)")
    p_update.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    p_update.set_defaults(func=cmd_update)

    # delete
    p_delete = sub.add_parser("delete", help="Delete a note")
    p_delete.add_argument("id", help="Note UUID")
    p_delete.add_argument("--permanent", action="store_true", help="Permanently delete (skip soft-delete)")
    p_delete.set_defaults(func=cmd_delete)

    # restore
    p_restore = sub.add_parser("restore", help="Restore a soft-deleted note")
    p_restore.add_argument("id", help="Note UUID")
    p_restore.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    p_restore.set_defaults(func=cmd_restore)

    # search
    p_search = sub.add_parser("search", help="Search notes by text")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("-c", "--case-sensitive", action="store_true")
    p_search.add_argument("-n", "--limit", type=int, help="Max results")
    p_search.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    p_search.set_defaults(func=cmd_search)

    # themes
    p_themes = sub.add_parser("themes", help="List valid theme names")
    p_themes.set_defaults(func=cmd_themes)

    args = parser.parse_args()
    args.func(args)
