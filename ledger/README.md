# The ledger — how a family looks out for each other

`family.py` is the coordination API. It is pure stdlib, has no dependencies, calls no
model, and works standalone. It writes one file (`cron_ledger.json`) next to itself and
best-effort commits it, so every agent in the family can see what every other agent did.

## Why it exists

Background agents fail quietly. A cron stops firing, a scrape returns nothing, a model
lane runs out of quota — and nothing tells you. You find out weeks later when you notice
the archive stopped growing.

The ledger is the smallest thing that fixes that: each member writes down that it ran and
what happened, so a sibling can notice when one of them goes silent.

## The four things it tracks

| Mechanism | What it answers |
|---|---|
| **Budget gate** (`run-gate`) | Should I work this cycle, given the shared budget? One toggle lowers the whole family. |
| **Check-in** (`check-in`) | I ran, here is my status and a one-line summary. |
| **Staleness** (`staleness`) | Who is overdue against their expected cadence? |
| **Shared state** (`dead-links`, `archive-growth`) | One member's discovery becomes everyone's knowledge. |

## Read this before you trust a red

**The ledger measures check-ins, not work.** A member can be doing its job perfectly and
show as overdue, because the step that was supposed to write to the ledger failed. We have
hit this twice: once because a git commit was silently failing inside a swallowed
exception, and once because the check-in was described in the cron prompt as a *reporting
item* rather than a *numbered step*.

So the rule is: **verify every staleness flag against the member's actual output artifacts
before you act on it.** Look for the files it was supposed to produce. If the files are
there, the problem is the check-in, not the work.

## Two limits worth knowing

- **Staleness limits are per-member and should be derived from cadence, not hand-set.** A
  member that runs every 6 hours and one that runs twice a week cannot share a threshold.
  Set `STALE_AFTER_HOURS` from the actual schedule. A limit that is too tight produces
  false reds, and false reds teach everyone to ignore the ledger — which is worse than no
  ledger.
- **A never-run member is not a failure.** Someone registered before their first scheduled
  run has no `last_run` yet. Render that as pending, not as red. Treating "hasn't run yet"
  as "broken" is how you train people to dismiss warnings.

## Before you add a member

1. Pick a name and put it in `STALE_AFTER_HOURS` with the limit derived from its schedule.
2. Make the check-in a **numbered step at the end of the cron prompt**, not a bullet in a
   summary section. Numbered steps get executed; report items get skipped.
3. Give it a job that is genuinely its own. Two members doing the same work will collide,
   and the ledger will not notice — that is what the lane registry is for.

## Known failure modes

See `../coordination/failure-modes.md`. The ledger's own code has carried two of them.
