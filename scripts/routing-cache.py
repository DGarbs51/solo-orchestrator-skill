#!/usr/bin/env python3
"""Store compact routing observations across local projects; never credentials."""
import argparse
import json
import os
from pathlib import Path
import sqlite3
import sys
from datetime import datetime, timezone

DEFAULT_TTL = {"catalog": 7200, "usage": 300, "outcome": None}


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError("observed_at must be an ISO timestamp string")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("observed_at must include a timezone")
    return result.timestamp()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, help="Override the machine-wide cache path")
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("get", "put", "list", "history"):
        p = sub.add_parser(command)
        p.add_argument("kind", choices=DEFAULT_TTL)
        if command != "list":
            p.add_argument("key")
        if command in ("list", "history"):
            p.add_argument("--limit", type=int, default=50, help="Maximum recent keys (default: 50)")
        if command == "put":
            p.add_argument("--file", type=Path, required=True, help="JSON observation file")
    args = parser.parse_args()
    if args.command in ("list", "history") and args.limit < 1:
        parser.error("--limit must be positive")
    root = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    db = args.db or root / "solo-orchestrator" / "routing.sqlite3"
    observation = None
    if args.command == "put":
        observation = json.loads(args.file.read_text())
        if not isinstance(observation, dict):
            raise ValueError("observation must be an object")
        if not isinstance(observation.get("source"), str) or not observation["source"].strip():
            raise ValueError("source must identify the command or observation")
        if not isinstance(observation.get("data"), dict):
            raise ValueError("data must be an object")
        observed = timestamp(observation["observed_at"])
        if observed > datetime.now(timezone.utc).timestamp() + 60:
            raise ValueError("observed_at is in the future")
    if not db.exists() and args.command != "put":
        print(json.dumps({"status": "missing", "records": []} if args.command in ("list", "history")
                         else {"status": "missing"}))
        return
    db.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db, timeout=5) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS observations (
            kind TEXT NOT NULL, key TEXT NOT NULL, observed REAL NOT NULL,
            payload TEXT NOT NULL, PRIMARY KEY(kind, key))""")
        conn.execute("""CREATE TABLE IF NOT EXISTS usage_history (
            key TEXT NOT NULL, observed REAL NOT NULL, payload TEXT NOT NULL,
            PRIMARY KEY(key, observed))""")
        if args.command == "put":
            if args.kind == "usage":
                conn.execute("INSERT OR IGNORE INTO usage_history VALUES (?, ?, ?)",
                             (args.key, observed, json.dumps(observation, allow_nan=False)))
                conn.execute("""DELETE FROM usage_history WHERE key=? AND observed NOT IN
                    (SELECT observed FROM usage_history WHERE key=? ORDER BY observed DESC LIMIT 200)""",
                    (args.key, args.key))
            cursor = conn.execute("""INSERT INTO observations VALUES (?, ?, ?, ?)
                ON CONFLICT(kind, key) DO UPDATE SET
                    observed=excluded.observed, payload=excluded.payload
                WHERE excluded.observed > observations.observed""",
                (args.kind, args.key, observed, json.dumps(observation, allow_nan=False)))
            result = {"status": "stored" if cursor.rowcount else "kept_existing"}
        elif args.command == "history":
            if args.kind != "usage":
                raise ValueError("history is supported only for usage")
            rows = conn.execute("SELECT payload FROM usage_history WHERE key=? ORDER BY observed DESC LIMIT ?",
                                (args.key, args.limit)).fetchall()
            result = {"status": "historical", "observations": [json.loads(row[0]) for row in rows]}
        elif args.command == "list":
            rows = conn.execute("SELECT key, observed FROM observations WHERE kind=? ORDER BY observed DESC, key LIMIT ?",
                                (args.kind, args.limit)).fetchall()
            result = {"records": [{"key": key, "observed_at": datetime.fromtimestamp(
                observed, timezone.utc).isoformat()} for key, observed in rows]}
        else:
            row = conn.execute("SELECT observed, payload FROM observations WHERE kind=? AND key=?",
                               (args.kind, args.key)).fetchone()
            result = {"status": "missing"}
            if row:
                age = max(0, datetime.now(timezone.utc).timestamp() - row[0])
                ttl = DEFAULT_TTL[args.kind]
                result = {"status": "historical" if ttl is None else
                          "fresh" if age < ttl else "stale", "age_seconds": round(age),
                          "observation": json.loads(row[1])}
        print(json.dumps(result))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError, sqlite3.Error) as exc:
        print(f"routing-cache: {exc}", file=sys.stderr)
        sys.exit(1)
