#!/usr/bin/env python3
"""family.py — the coordination ledger for a family of research agents.

A lean, pure-stdlib API (no dependencies, no LLM) that agents use to look
out for each other: budget gate, staleness watchdog, known-dead links,
archive growth. Writes cron_ledger.json in this folder and best-effort
commits it to git (works standalone too).

Place this file in your cron-coordination shared repo. Every agent with a
cron uses it from there. Always git pull --rebase before reading, push after
writing (or let the auto-commit push for you when the repo is attached).

CLI:
  python3 family.py check-in --member NAME --status ok --summary "..." [--entries-count N] [--budget-mode high|low|normal]
  python3 family.py run-gate --member NAME [--essential]          # exit 0 = run, exit 1 = skip
  python3 family.py staleness                                      # list overdue members
  python3 family.py dead-links --add URL [URL ...]                 # share a dead link
  python3 family.py dead-links                                     # list known dead
  python3 family.py archive-growth --entries N                     # report DB size
  python3 family.py set-budget --mode low                          # one toggle, whole family
  python3 family.py show                                           # full status

Python API:
  import family
  run, reason = family.should_run("scout", essential=True)
  family.check_in("scout", "ok", "5 finds saved", entries_count=42)
  family.staleness_report()
"""
import argparse, json, os, subprocess, sys, time, datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LEDGER_DIR = os.environ.get("LEDGER_DIR", SCRIPT_DIR)
LEDGER_FILE = os.path.join(LEDGER_DIR, "cron_ledger.json")

# How long a member may stay silent before being flagged (hours).
# New/unlisted members default to 24h. Tune as your cadence evolves.
STALE_AFTER_HOURS = {"scout": 18, "scribe": 18, "librarian": 40}

_dt = lambda ts: datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)


def _default_ledger():
    return {
        "version": 1,
        "family_budget": {"mode": "high", "last_set": _now_iso(), "intent": ""},
        "members": {},
        "shared": {"known_dead_links": [], "archive_growth": {"last_entry_count": None, "last_reported": None, "added_since_last": 0}},
    }


def _now_iso():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _now_ts():
    return time.time()


GIT_FAILURES_LOG = os.path.join(LEDGER_DIR, "ledger_push_failures.log")


def _git(*args, timeout=20):
    """Run a git command in LEDGER_DIR. Returns (ok, detail). Never raises."""
    try:
        p = subprocess.run(["git", "-C", LEDGER_DIR, *args],
                           capture_output=True, text=True, timeout=timeout)
        if p.returncode != 0:
            out = (p.stderr or p.stdout or "").strip().splitlines()
            return False, (out[-1] if out else "exit %d" % p.returncode)
        return True, ""
    except FileNotFoundError:
        return False, "git not found on PATH"
    except Exception as e:
        return False, "%s: %s" % (type(e).__name__, e)


def _note_failure(step, detail):
    """Record a sync failure to a log file AND to stderr.

    Silence is the bug this exists to prevent. A family whose ledger has not
    synced for weeks looks identical to a family where nobody is working — and
    the second one is the only one you should be alarmed by.
    """
    line = "%s %s FAILED: %s" % (_now_iso(), step, detail)
    try:
        with open(GIT_FAILURES_LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    print("WARNING: ledger not synced — " + line, file=sys.stderr)


def load():
    try:
        with open(LEDGER_FILE, encoding="utf-8") as f:
            d = json.load(f)
        d.setdefault("family_budget", _default_ledger()["family_budget"])
        d.setdefault("members", {})
        d.setdefault("shared", _default_ledger()["shared"])
        d["shared"].setdefault("known_dead_links", [])
        d["shared"].setdefault("archive_growth", _default_ledger()["shared"]["archive_growth"])
        return d
    except Exception:
        return _default_ledger()


def save(d):
    """Write the ledger, then best-effort sync it to git.

    Non-git use is expected and stays quiet. Every OTHER failure is recorded —
    see _note_failure. Do not change this back to a bare `except: pass`: doing
    so makes a broken sync indistinguishable from a quiet family.
    """
    with open(LEDGER_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

    ok, detail = _git("pull", "--rebase", "--quiet")
    if not ok:
        if "not a git repository" in detail:
            return  # standalone use — expected
        _note_failure("pull", detail)
        return

    ok, detail = _git("add", "cron_ledger.json")
    if not ok:
        _note_failure("add", detail)
        return

    ok, detail = _git("commit", "-m", "family ledger update")
    if not ok and "nothing to commit" not in detail:
        _note_failure("commit", detail)
        return

    ok, detail = _git("push", "--quiet", timeout=30)
    if not ok:
        _note_failure("push", detail)


# ---------- API ----------

def should_run(member, essential=False):
    """Budget gate. Returns (run: bool, reason: str)."""
    d = load()
    mode = d["family_budget"].get("mode", "high")
    if mode == "low" and not essential:
        return False, f"family budget low; member {member} skipped (non-essential)"
    return True, f"budget {mode}; run allowed"


def check_in(member, status="ok", summary="", entries_count=None, budget_mode=None):
    """Record a run result. Returns the ledger dict."""
    d = load()
    d["members"][member] = {
        "last_run": _now_iso(),
        "last_status": status,
        "last_summary": summary[:500],
        "last_details": {"entries_count": entries_count, "budget_mode": d["family_budget"].get("mode")},
    }
    if budget_mode:
        d["family_budget"] = {"mode": budget_mode, "last_set": _now_iso(), "intent": "set by member check-in"}
    if entries_count is not None:
        g = d["shared"]["archive_growth"]
        prev = g.get("last_entry_count")
        g["added_since_last"] = (entries_count - prev) if isinstance(prev, int) else 0
        g["last_entry_count"] = entries_count
        g["last_reported"] = _now_iso()
    save(d)
    return d


def staleness_report(now=None):
    """Return list of overdue members (name, hours_since_run, limit)."""
    d = load()
    now = now if now is not None else _now_ts()
    out = []
    for member, rec in d["members"].items():
        try:
            last = datetime.datetime.strptime(rec["last_run"], "%Y-%m-%dT%H:%M:%SZ")
            hours = (now - last.timestamp()) / 3600
        except Exception:
            continue
        limit = STALE_AFTER_HOURS.get(member, 24)
        if hours > limit:
            out.append((member, round(hours, 1), limit))
    return out


def record_dead_links(urls):
    d = load()
    for u in urls:
        if u not in d["shared"]["known_dead_links"]:
            d["shared"]["known_dead_links"].append(u)
    save(d)
    return d["shared"]["known_dead_links"]


def report_archive_growth(entries):
    d = load()
    g = d["shared"]["archive_growth"]
    prev = g.get("last_entry_count")
    g["added_since_last"] = (entries - prev) if isinstance(prev, int) else 0
    g["last_entry_count"] = entries
    g["last_reported"] = _now_iso()
    save(d)
    return g


def set_budget(mode, intent=""):
    d = load()
    d["family_budget"] = {"mode": mode, "last_set": _now_iso(), "intent": intent}
    save(d)
    return d["family_budget"]


def show():
    return load()


# ---------- CLI ----------

def main():
    p = argparse.ArgumentParser(description="family ledger API")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check-in")
    c.add_argument("--member", required=True)
    c.add_argument("--status", default="ok")
    c.add_argument("--summary", default="")
    c.add_argument("--entries-count", type=int, default=None)
    c.add_argument("--budget-mode", choices=["high", "normal", "low"], default=None)

    c = sub.add_parser("run-gate")
    c.add_argument("--member", required=True)
    c.add_argument("--essential", action="store_true")

    sub.add_parser("staleness")

    c = sub.add_parser("dead-links")
    c.add_argument("--add", nargs="*", default=None)

    c = sub.add_parser("archive-growth")
    c.add_argument("--entries", type=int, required=True)

    c = sub.add_parser("set-budget")
    c.add_argument("--mode", choices=["high", "normal", "low"], required=True)
    c.add_argument("--intent", default="")

    sub.add_parser("show")

    a = p.parse_args()

    if a.cmd == "check-in":
        check_in(a.member, a.status, a.summary, a.entries_count, a.budget_mode)
        print(f"check-in recorded: {a.member} ({a.status})")
    elif a.cmd == "run-gate":
        run, reason = should_run(a.member, essential=a.essential)
        print(reason)
        sys.exit(0 if run else 1)
    elif a.cmd == "staleness":
        stale = staleness_report()
        if stale:
            for m, h, lim in stale:
                print(f"STALE: {m} (last run {h}h ago, limit {lim}h)")
        else:
            print("all members current")
    elif a.cmd == "dead-links":
        if a.add:
            links = record_dead_links(a.add)
            print(f"recorded; {len(links)} known dead total")
        else:
            for u in load()["shared"]["known_dead_links"]:
                print(u)
    elif a.cmd == "archive-growth":
        g = report_archive_growth(a.entries)
        print(f"entries {g['last_entry_count']} (+{g['added_since_last']} since last)")
    elif a.cmd == "set-budget":
        b = set_budget(a.mode, a.intent)
        print(f"budget set: {b['mode']}")
    elif a.cmd == "show":
        print(json.dumps(load(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()