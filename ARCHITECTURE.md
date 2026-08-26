# Architecture — the thinking behind the kit

One sentence: **one shared commons, three specialists, cheap scheduled crons,
coordinated through a ledger.**

The whole design exists so that the system grows itself over time with minimal
attention and minimal cost. This file explains each piece and *why* it's built
this way — so you can extend it when your needs outgrow these three roles.

---

## 1. The commons (shared memory)

**What:** a git-backed repo on Letta Cloud (`living-library`) that every agent
attaches. Structure:

```
living-library/
├── sources/        # raw finds: articles, papers, links, PDFs — with provenance
├── translations/   # English translations, one file per source
├── database/       # structured records: persons, research works, patents, taxonomy
└── taxonomy/       # the concept vocabulary (terms → concepts → themes)
```

**Why it matters:** if agents kept findings in their own memory, three agents
would build three silos. The commons makes every agent's work visible to every
other agent and to you. It is *not* a backend — it's a git repo, so you can
read it with any tool, any machine, anytime.

**Rule:** pull with `--rebase` before reading, push after writing. Other
agents may have written since your last pull.

## 2. The specialists (one job each)

| Agent | Job | Needs LLM judgment? | Model tier |
|---|---|---|---|
| **Scout** | Search multilingual web for rare/disappearing material; run scrapers; save finds with provenance | Low (mostly mechanical) | Free / rotating |
| **Scribe** | Translate non-English finds to English; chunk long books; batch-translate; assemble | High per unit of work | Quality (BYOK) |
| **Librarian** | Ingest finds into structured database; maintain taxonomy; run deterministic taggers; rebuild indexes | Low (scripts do the work) | Free |

**Why three narrow agents instead of one generalist:** each card is short and
each cron is cheap. A generalist that "does everything" needs a huge prompt,
fires expensively, and does a worse job at each specialty. Narrow agents also
parallelize — Scout can be mid-hunt while Scribe is mid-translation.

## 3. The ledger (coordination layer)

`family.py` + a small JSON file (`cron_ledger.json`) in the shared
`cron-coordination` repo. The family looks out for each other:

- **Budget gate** — before working, check the shared budget. If it's `low`,
  non-essential members skip that cycle (and say `skipped` in the ledger, so
  nobody thinks they died).
- **Staleness watchdog** — each member records `last_run`. If a sibling
  hasn't run in too long, the next member to wake flags it. Silent failures
  get caught in hours, not weeks.
- **Known-dead links** — one member's link-check failures become a shared
  list everyone respects.
- **Archive growth** — when the database grows, the ledger records it, so any
  member (or a site builder) can surface fresh content.

**The four commands you'll actually use:**

```bash
python3 family.py run-gate --member scout --essential   # should I run this cycle?
python3 family.py check-in --member scout --status ok --summary "5 finds saved"
python3 family.py staleness                              # who's overdue?
python3 family.py show                                   # whole family status
```

## 4. The economy (making it survive on cheap credits)

The lessons from running a real family for weeks:

1. **Batch, don't drip.** A 6-hour cron that processes a full batch is ~4×
   cheaper than firing every 15 minutes. Fewer, bigger fires.
2. **The model ladder.** Free/rotating models for mechanical work (Scout,
   Librarian), one cheap BYOK quality model for Scribe's translation, and
   interactive quota only for you chatting with agents. Don't burn reasoning
   credits on a loop that greps a file list.
3. **Budget gate as a fuse.** When credits are tight, set the ledger budget to
   `low` once and every non-essential member self-throttles. One toggle, whole
   family.
4. **Self-healing crons.** Scripts are idempotent (safe to re-run), checkpoints
   progress in files (a manifest, a progress JSON), and commit+push after each
   batch. If a cron dies, the next run picks up where it left off.

## 5. The layering (terms → concepts → themes → clusters)

The data model that makes cross-referencing rewarding (learned building the
REX Vault's comparison layer):

- **L1 — Terms:** raw vocabulary in the text (filenames, titles, previews).
- **L2 — Concepts:** normalized ideas, each with alias terms (e.g. `torsion`
   matches "torsion field", "spin field"; `overunity` matches "free energy",
   "over-unit"). Curated once in `taxonomy/concepts.json`.
- **L3 — Themes / concept groups:** broad categories (your 23 meta-themes)
   assembled FROM concepts, not hand-authored per document.
- **L4 — Thought clusters:** **emergent** — which concepts co-occur across the
   corpus. Computed at query time, not curated. This is the "nitty-gritty
   cross-referencing" layer.

**Why this order:** documents get tagged deterministically from L2 (a cheap
regex matcher against the vocabulary — no LLM per document, so it scales to
tens of thousands of docs for $0). Themes and clusters then fall out of the
tags. Layer intentionally, and every level stays consistent because it's
derived, not hand-maintained.

## Scaling to more agents

Adding a fourth role (e.g. a **Site Builder** that publishes the database to a
public site, or a **Watchdog** that validates links) is just: new agent card,
attach both shared repos, add a cron, pick a member name and a staleness
limit. The ledger and commons are role-agnostic.