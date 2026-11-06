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

Staleness readings carry their own provenance (2026-11-06): the CLI
`staleness` command and `staleness_report_stamped()` stamp when the report
ran and how fresh its ledger input was, because a stale-flag built on a
stale surface is a false flag (connector r56-r58; watchtower Issues 4-5).

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
# RULE: a limit must exceed the member's cadence PLUS the sync period of the
# surface it is read from — a 2-day-cadence lane read through an every-other-day
# mirror at a 19.7h limit flags stale at every check (the takedown-watch lesson,
# connector r56/r57; ported by Watchtower, Issue 5, 2026-11-06).
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


def check_in(member, status="ok", summary="", entries_count=None, budget_mode=None, visible_at=None):
    """Record a run result. Returns the ledger dict.

    `visible_at` (optional, ISO): when this row became visible on the surface
    being read — set by a mirror/sync operator when it merges an org-side
    check-in, so readers can compute propagation delay (visible_at - last_run)
    and a closing instrument can tell real silence from unsynced silence.
    Direct writers leave it None (defaults to last_run at read time).
    """
    d = load()
    row = {
        "last_run": _now_iso(),
        "last_status": status,
        "last_summary": summary[:500],
        "last_details": {"entries_count": entries_count, "budget_mode": d["family_budget"].get("mode")},
    }
    if visible_at:
        row["visible_at"] = visible_at
    d["members"][member] = row
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


def _input_stamp():
    """Best-effort provenance of the ledger input: git HEAD of LEDGER_DIR
    (when it is a repo) plus the ledger file's mtime. Pull before trusting."""
    head = None
    try:
        r = subprocess.run(["git", "-C", LEDGER_DIR, "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            head = r.stdout.strip()
    except Exception:
        pass
    mtime = None
    try:
        mtime = _dt(os.path.getmtime(LEDGER_FILE)).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        pass
    return {"ledger": LEDGER_FILE, "git_head": head, "ledger_mtime": mtime,
            "note": "git pull --rebase before trusting flags"}


def staleness_report_stamped(now=None):
    """Staleness reading with its own provenance (2026-11-06 port of the
    watchtower/staleness_report.py stamps fix, per connector r58 clause 4:
    "the connector-side staleness run stamps its input").

    Returns a dict:
      {"run_at": iso,                # when THIS report ran
       "input": {...},              # _input_stamp(): how fresh the input was
       "stale": [ {"member", "hours_since_run", "limit", "verdict", ...} ]}

    Verdicts:
      "stale"             — the row is overdue on a fresh-enough surface.
      "possibly-unsynced" — the row is overdue AND the input surface itself is
                            older than the member's limit, so the silence may
                            be a sync lag, not a stall. Re-pull before acting.
    Rows carrying "visible_at" also report propagation_delay_h (visible_at
    minus last_run) — how long the check-in took to reach this surface.
    """
    run_at = _now_iso()
    inp = _input_stamp()
    input_age_h = None
    if inp.get("ledger_mtime"):
        try:
            m = datetime.datetime.strptime(inp["ledger_mtime"], "%Y-%m-%dT%H:%M:%SZ")
            input_age_h = round(((now if now is not None else _now_ts()) - m.timestamp()) / 3600, 1)
        except Exception:
            input_age_h = None
    out = []
    for member, hours, limit in staleness_report(now=now):
        rec = load()["members"].get(member, {})
        verdict = "stale"
        if input_age_h is not None and input_age_h > limit:
            verdict = "possibly-unsynced"
        entry = {"member": member, "hours_since_run": hours, "limit": limit, "verdict": verdict}
        va = rec.get("visible_at")
        if va:
            try:
                v = datetime.datetime.strptime(va, "%Y-%m-%dT%H:%M:%SZ")
                l = datetime.datetime.strptime(rec["last_run"], "%Y-%m-%dT%H:%M:%SZ")
                entry["visible_at"] = va
                entry["propagation_delay_h"] = round((v - l).total_seconds() / 3600, 1)
            except Exception:
                pass
        out.append(entry)
    return {"run_at": run_at, "input": inp, "input_age_h": input_age_h, "stale": out}


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
        stamped = staleness_report_stamped()
        print(f"run: {stamped['run_at']}")
        head = stamped["input"].get("git_head")
        src = f"git HEAD {head}" if head else f"ledger mtime {stamped['input'].get('ledger_mtime')}"
        print(f"input: {src} — {stamped['input']['note']}")
        if stamped["stale"]:
            for e in stamped["stale"]:
                line = f"STALE: {e['member']} (last run {e['hours_since_run']}h ago, limit {e['limit']}h)"
                if e["verdict"] == "possibly-unsynced":
                    line += f" [possibly-unsynced: input surface {stamped['input_age_h']}h old — re-pull before acting]"
                if "propagation_delay_h" in e:
                    line += f" [propagation delay {e['propagation_delay_h']}h]"
                print(line)
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
