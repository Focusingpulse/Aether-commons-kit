# Aether Commons Kit

A ready-to-run handoff kit for setting up a **three-agent research family** on
Letta — one shared growing database, three specialists, cheap scheduled crons,
and a ledger that keeps them coordinated.

Built from real lessons running the Aetherforce Knowledge Vault (AFLinks):
over **90,000** documents, a 5-volume book translation pipeline, a multi-site
scraping queue, and a family of background agents that have been running for
months.

It also carries the part most kits leave out — **the security rules and the
failure modes**, each one written down because we got it wrong first.

## What you get

```
aether-commons-kit/
├── README.md            ← you are here
├── ARCHITECTURE.md      ← the full blueprint: commons, specialists, ledger, economy
├── SECURITY.md          ← secrets, keys, access, and what leaks
├── STRUCTURES.md        ← LLCs, trusts, PMAs, 508(c)(1)(a) churches: the map and the traps
├── agents/
│   ├── scout.md         ← card: the FINDER (rare texts, declassified docs, scraping)
│   ├── scribe.md        ← card: the TRANSLATOR (non-English → English)
│   └── librarian.md     ← card: the DATABASE BUILDER (structured records, tagging)
├── commons/
│   └── README.md        ← what the shared database IS and how to keep it clean
├── coordination/        ← how the family governs itself
│   ├── README.md        ← the six mechanisms, and which one to build first
│   ├── lane-registry.md ← who owns what, so nobody collides
│   ├── review-queue.md  ← nobody ships their own work
│   ├── boundaries.md    ← what may leave the house (three tiers + intake lane)
│   └── failure-modes.md ← the ten ways this breaks quietly
├── ledger/
│   ├── family.py        ← the coordination API (budget gate, staleness, dead links)
│   └── README.md        ← how the family looks out for each other
└── scripts/
    ├── chunk_book.py        ← split a long book into translatable chunks
    └── assemble_translation.py ← stitch translated chunks into a full document
```

## Quick start (about 20 minutes)

**1. Install Letta** (if you haven't): `curl -fsSL https://letta.com/install.sh | bash`
— or use the Desktop app. Create an account.

**2. Create the shared commons** (once, from any machine):

```bash
letta shared-memory create <yourname>-commons
letta shared-memory create <yourname>-coordination
```

These are git-backed repos on Letta Cloud. Every agent attaches them, so all
three agents see the same growing database. This is the single source of truth.

**Prefix both names with your own handle.** Shared-memory names are global to
your account but people copy these instructions verbatim, and three families all
naming a repo `living-library` makes every example, log, and error message
ambiguous. Use your own prefix.

**3. Create the three agents:**

```bash
letta agent create --name scout     --description "Finds rare texts, declassified docs, and scrapes archives"
letta agent create --name scribe    --description "Translates non-English finds into English, in batches"
letta agent create --name librarian --description "Builds the structured database and keeps the taxonomy clean"
```

Then, on **each** agent:

```bash
letta shared-memory attach <yourname>-commons
letta shared-memory attach <yourname>-coordination
```

**4. Set up the coordination (once):** copy `ledger/family.py` into your
coordination repo (it becomes the shared ledger API). Then read
`coordination/README.md` — it lists six mechanisms in the order you actually
need them. Build the first two now. The rest wait until you have a reason.

**5. Add the crons:** for each agent, paste the cron prompt from its card
(`agents/scout.md`, `agents/scribe.md`, `agents/librarian.md`) into
`letta cron add`. Exact commands are at the bottom of each card.

**6. Watch it grow.** Every cycle each agent saves finds / translations /
database records into the commons and checks in to the ledger. Run
`python3 family.py show` in the ledger repo to see the whole family's status.

## House rules (from real mistakes)

1. **Data-first.** The database is the resource; the interface is just a window.
   Build the DB before any frontend.
2. **Additive only.** Never overwrite an original with a translated version —
   translations are separate files next to the source. Tags layer ON, never replace.
3. **Provenance on everything.** Every find carries source URL + who found it
   + when. "Where did this come from" is always answerable.
4. **Batch, don't drip.** One job every 6h that does real work is ~4× cheaper
   than the same work trickled out. Crons fire rarely but fully.
5. **The counter is the heartbeat.** If the database grows every cycle, the
   system is alive. If it stalls, the watchdog in the ledger says who slept.

## Read this before you put anything online

`SECURITY.md` is short and every line in it cost us something. If you read one
file in this kit before going public, read that one.

`STRUCTURES.md` is the other one people ask for. If you are considering a trust,
a private membership association, a 508(c)(1)(a) church, or a US entity while
living outside the US, read it **before you pay anyone.** It maps each instrument
to the goal it actually serves, and it names the promoter patterns from IRS
sources so you can recognise them.

`coordination/boundaries.md` is the one everyone skips, because nothing goes wrong
on the day you skip it — it goes wrong a year later, when it cannot be undone.
Write your policy *before* you have something to publish. A boundary decided in
advance is a policy; a boundary decided at the moment of maximum excitement is a
gamble.

## Pedagogical note

This kit is also a lesson in *delegation*. Each agent card names the same four
things for a good handoff: **the outcome, the context, the boundaries, and
what "done" looks like.** Every cron prompt in `agents/` follows that shape —
steal the shape for any agent you add later.

Start with **one agent** (Scout) for a week, prove the loop, then add the
other two cards. The architecture is identical at one agent as at three.

---

👾 Generated with [Letta Code](https://letta.com)