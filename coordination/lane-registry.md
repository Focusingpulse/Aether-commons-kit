# The lane registry

A lane is a job someone owns. The registry is one table that says who owns what, so two
members do not quietly duplicate each other and two write targets do not collide.

## The table

Copy this shape and fill it in. One row per lane.

| Lane | Producer | Consumes | Writes to | Cadence | Owner |
|---|---|---|---|---|---|
| e.g. `find-sources` | Scout | search, commons/sources | `commons/sources/` | 6h | _name_ |
| e.g. `translate` | Scribe | commons/sources, commons/translations | `commons/translations/` | 12h | _name_ |
| e.g. `index` | Librarian | commons/* | `commons/database/` | 6h | _name_ |

**The column that matters most is `Writes to`.** Two members writing the same path is the
collision you are trying to prevent, and it is invisible until something gets overwritten.

---

## The four collision rules

**1. Before you build any artifact, search for one that already exists.**
Scan, audit, report, index — before writing a new one, grep the repo for an existing
artifact on the same subject and the same day. This has cost us a duplicated day of work
more than once. Look first; the artifact is often already there.

**2. Quote the denominator your action needs, and say which one it is.**
The same finding can be counted two ways and both be correct: *how many targets need
fixing* versus *how bad is it*. One instance count and one target count described the same
problem, and they differed by five times. Both were right. Only one of them set the
priority. Name which number you are quoting.

**3. Append-only logs merge by union, never by choosing a side.**
Threads, changelogs, strength ledgers — if two writers touch the same append-only file,
restore from the remote and re-append your entry. Picking "mine" on a conflict deletes the
other writer's entry, and you will not notice, because your version looks complete.

**4. Expect self-collision.**
Two *separate sessions of the same agent* can race on the same resource at the same time.
This is not a multi-agent problem; it is a same-agent problem, and it happens whenever a
job is triggered from more than one place. If a resource is written by a scheduled job,
assume a human session may also be in it.

---

## On ownership

Ownership in a small family is **coordination hygiene, not property.** The registry exists
so two people do not spend the same hour twice. It is not a fence, and nobody should be
blocked from fixing something urgent because a table says a lane is theirs.

What the registry actually prevents is the expensive failure: two members independently
building the same scan on the same day, each thinking they were being helpful.

## When a lane is retired

A retired lane that still shows in the ledger as stale will produce a permanent false red,
and false reds are how a monitoring system loses its authority. Mark it retired explicitly
and have the staleness check skip retired members. Do not just delete the row — the reason
it was retired is worth keeping.
