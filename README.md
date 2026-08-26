# Aether Commons Kit

A ready-to-run handoff kit for setting up a **three-agent research family** on
Letta — one shared growing database, three specialists, cheap scheduled crons,
and a ledger that keeps them coordinated.

Built from real lessons running the Aetherforce Knowledge Vault (AFLinks):
7,200+ documents, a 5-volume book translation pipeline, 13-site scraping
queue, and a family of background agents that have been running for weeks.

## What you get

```
aether-commons-kit/
├── README.md            ← you are here
├── ARCHITECTURE.md      ← the full blueprint: commons, specialists, ledger, economy
├── agents/
│   ├── scout.md         ← card: the FINDER (rare texts, declassified docs, scraping)
│   ├── scribe.md        ← card: the TRANSLATOR (non-English → English)
│   └── librarian.md     ← card: the DATABASE BUILDER (structured records, tagging)
├── commons/
│   └── README.md        ← what the shared database IS and how to keep it clean
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
letta shared-memory create living-library
letta shared-memory create cron-coordination
```

These are git-backed repos on Letta Cloud. Every agent attaches them, so all
three agents see the same growing database. This is the single source of truth.

**3. Create the three agents:**

```bash
letta agent create --name scout     --description "Finds rare texts, declassified docs, and scrapes archives"
letta agent create --name scribe    --description "Translates non-English finds into English, in batches"
letta agent create --name librarian --description "Builds the structured database and keeps the taxonomy clean"
```

Then, on **each** agent:

```bash
letta shared-memory attach living-library
letta shared-memory attach cron-coordination
```

**4. Set up the coordination (once):** copy `ledger/family.py` into your
`cron-coordination` repo (it becomes the shared ledger API).

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

## Pedagogical note

This kit is also a lesson in *delegation*. Each agent card names the same four
things for a good handoff: **the outcome, the context, the boundaries, and
what "done" looks like.** Every cron prompt in `agents/` follows that shape —
steal the shape for any agent you add later.

Start with **one agent** (Scout) for a week, prove the loop, then add the
other two cards. The architecture is identical at one agent as at three.

---

👾 Generated with [Letta Code](https://letta.com)