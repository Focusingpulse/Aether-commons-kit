# Failure modes — the ways this breaks quietly

Every one of these happened to us. They share one property: **the system reported success.**
That is what makes them expensive — a loud failure costs an hour, and a quiet one costs a
month.

---

## 1. The swallowed error

```python
try:
    do_the_important_thing()
except Exception:
    pass
```

The important thing stops happening and every caller is told it worked. Ours: a git commit
inside a coordination script that failed for weeks because a required binary was missing
from the path — and the script said `status: ok` the whole time.

**Fix:** never wrap a critical step in a bare `except: pass`. Either let it fail loudly, or
catch it and *record the failure somewhere a human will see it*. A failure that prints
nothing is not handled, it is hidden.

## 2. The check that cannot fail

If a monitor reads its threshold from the same artifact it is monitoring, it compares the
value to itself and always passes. Ours: a counter regression check whose floor came from
the last published row — which *was* the row being checked.

**Fix:** the two sides of a check must come from different sources. And prove the check
*can* fail before you trust it when it passes.

## 3. The operation that cannot be rejected

A push built to always fast-forward, so it can never be refused — and therefore cannot
notice it is pointed at the wrong source. Exit 0, success-shaped logs, wrong content.

**Fix:** when a design removes a failure mode, ask which failure it removed the ability to
**detect**.

## 4. The silent skip

A branch that drops an item without printing anything. Ours: a parser that skipped
malformed references inside `try/except: continue`, dropping four of ten records with no
output. The summary line said it processed everything.

**Fix:** a skip must print a count. `unlinked refs: 4` on the summary line turns a silent
data-loss channel into a visible one.

## 5. The hand-set threshold

Staleness limits set by intuition rather than derived from the actual cadence. A member
that runs every 6 hours and one that runs twice a week cannot share a number.

**Fix:** derive the limit from the schedule, and revisit when the schedule changes. A
threshold that is too tight produces false alarms, and false alarms teach everyone to
ignore the system.

## 6. Never-run treated as broken

A member registered before its first run has no last-run timestamp. Sorting or comparing
against `None` either crashes the report or paints a red.

**Fix:** "has not run yet" is its own state — render it as pending, not as failure. And
never let a new member's null field take down the whole report; that is how one missing
field blanks the entire dashboard.

## 7. The public surface that leaks

You scrub the source files and the rendered page still carries the names, because the
names came from ledger entries, tags, and database fields you never thought of as content.

**Fix:** grep the **rendered output**, not the source. Assume every public surface leaks
until proven otherwise, and re-verify after any change to what feeds it.

## 8. The unattached repo

You search everywhere you can read, find no explanation, and conclude the cause does not
exist. Ours: fifteen hours across seven monitoring runs spent on two "mysteries" that were
one commit, in a repository that was not attached to the machine doing the searching.

**Fix:** when a search for a cause comes back empty, widen the search space **before**
concluding the cause is absent. And if the evidence lives somewhere you have not attached,
attach it rather than reasoning around it.

---

## 9. And the one about the artifact that was never written

Not a code failure. A documentation one, and worth its own entry because it is the most
quietly corrosive.

A summary says *"full detail is in `path/to/report.md`."* The file does not exist. Nobody
written it. The pointer reads as recoverable, so nobody goes back and re-derives the
detail — and the finding degrades from "documented" to "vaguely remembered" without anyone
deciding to let it.

**Fix:** a pointer to an artifact is a claim about the filesystem. If you reference a file,
create it in the same breath. Do not hand over a path you have not confirmed exists.

---

## 10. The substring match that always fires

A leak scan looking for the word `tutor` matched `statutory`. Twice. Both hits were inside quotations of legal text.

Without word boundaries, a keyword scan of any long document will find something, and the finding will be meaningless. The worse case is the mirror image: a scan whose pattern cannot match looks identical to a scan that found nothing, so you conclude the surface is clean.

**Fix:** use word boundaries, scan for the *pattern* you actually care about rather than the topic word, and when a scan does fire, read **what** matched before deciding it is benign.

And the discipline that matters more than the regex: **a scan result you did not inspect is not a result.** Reporting "clean" from a non-empty scan is the same error as reporting a zero without checking the pattern.

---

## The pattern behind all ten

Each one is a check, a log, or a guard that was **structurally incapable of reporting the
problem it existed to catch.**

So the single question to ask of any monitoring you build: *if this broke right now, what
would I see?* If the answer is "nothing," you have built one of these, and the fix is
almost always to make it able to fail loudly rather than to make it better at passing.
