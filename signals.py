"""Materialize one Jev decision per distinct QuestDB log template."""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from jev import evaluate, fixture_evaluator


def validate_write_url(url):
    parsed = urlsplit(url)
    if (not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.path != "/write" or parsed.scheme not in ("https", "http")
            or (parsed.scheme == "http" and parsed.hostname not in ("localhost", "127.0.0.1", "::1"))):
        raise ValueError("invalid_questdb_url")
    return url


@contextmanager
def open_state(path):
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE IF NOT EXISTS decisions (template_hash TEXT NOT NULL, policy_version TEXT NOT NULL, choice TEXT NOT NULL, outcome TEXT NOT NULL, probability REAL NOT NULL, PRIMARY KEY(template_hash, policy_version))")
    try:
        yield db
    finally:
        db.close()


def to_ilp(template_hash, result):
    if (not re.fullmatch(r"[0-9a-f]{64}", template_hash)
            or any(not isinstance(result.get(name), str) or
                   not re.fullmatch(r"[A-Za-z0-9._-]{1,64}", result[name])
                   for name in ("policy_version", "choice", "outcome"))):
        raise ValueError("invalid_ilp_identifier")
    return (f"jev_signals,template_hash={template_hash},policy_version={result['policy_version']} "
            f"choice=\"{result['choice']}\",outcome=\"{result['outcome']}\","
            f"probability={result['probability']}\n")


def send_ilp(url, line, *, opener=urlopen):
    request = Request(validate_write_url(url), data=line.encode(),
                      headers={"Content-Type": "text/plain; charset=utf-8"}, method="POST")
    with opener(request, timeout=15) as response:
        response.read()


def process(lines, db, policy, judge, publish):
    sent = 0
    for line in lines:
        if not line.strip():
            continue
        row = json.loads(line)
        template = row.get("template") if isinstance(row, dict) else None
        if not isinstance(template, str) or not template.strip() or len(template) > 16000:
            raise ValueError("invalid_template")
        digest = hashlib.sha256(template.encode()).hexdigest()
        if db.execute("SELECT 1 FROM decisions WHERE template_hash=? AND policy_version=?",
                      (digest, policy["version"])).fetchone():
            continue
        result = judge(template)
        ilp = to_ilp(digest, result)
        publish(ilp)
        db.execute("INSERT INTO decisions VALUES (?,?,?,?,?)",
                   (digest, policy["version"], result["choice"], result["outcome"], result["probability"]))
        db.commit()
        sent += 1
    return sent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="JSONL rows with a template string")
    parser.add_argument("--policy", default="examples/policy.json")
    parser.add_argument("--fixtures", help="offline template-to-decision JSON mapping")
    parser.add_argument("--push", action="store_true", help="send decisions to QuestDB /write")
    parser.add_argument("--state", default=":memory:", help="SQLite state path (required for --push)")
    args = parser.parse_args()
    if args.push and args.state == ":memory:":
        parser.error("--push requires persistent --state")
    with open(args.policy, encoding="utf-8") as source:
        policy = json.load(source)
    if args.fixtures:
        with open(args.fixtures, encoding="utf-8") as source:
            judge = fixture_evaluator(json.load(source), policy)
    else:
        key = os.environ["TYPESAFE_API_KEY"]
        judge = lambda template: evaluate(template, policy, key)
    if args.push:
        url = validate_write_url(os.environ["QUESTDB_WRITE_URL"])
        publish = lambda ilp: send_ilp(url, ilp)
    else:
        publish = lambda ilp: print(ilp, end="")
    with open(args.input, encoding="utf-8") as source, open_state(args.state) as db:
        process(source, db, policy, judge, publish)


if __name__ == "__main__":
    main()
