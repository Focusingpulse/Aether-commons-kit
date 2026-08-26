# The Commons — what this folder is and how to keep it clean

The `living-library` shared repo. Every agent attaches it. If it's not in
here, it doesn't exist.

```
commons/            → (in the real repo: the repo root)
├── sources/        # raw finds: articles, papers, links, PDFs
│                   # file: YYYY-MM-DD-scout.md (numbered entries, URLs, why-it-matters)
├── translations/   # English translations
│                   # file: YYYY-MM-DD-<topic>-<lang>.md — NEVER overwrite the source
├── database/       # structured records
│   ├── persons/    #   researchers, scientists, thinkers
│   ├── research/   #   works: papers, books, patents, experiments
│   ├── patents/    #   patent numbers, domain-mapped
│   └── taxonomy/   #   categories + the concept vocabulary (concepts.json)
```

## Conventions (the house rules)

1. **Provenance on everything.** A find without a source URL, a date, and a
   finder name is noise. Save it anyway, label it noise, but always keep the
   trail.
2. **Additive only.** Transcriptions, translations, tags, and records layer
   ON. Never `rm` or overwrite someone else's file. If a record is wrong, add
   a correction next to it — don't erase history.
3. **One file per unit.** A scout report is one dated file. A translation is
   one dated file. A book's chunks are one folder + one manifest.
4. **Idempotent scripts.** Anything the crons run must be safe to re-run:
   merging by URL, chunking by manifest, tagging by id. No "delete and
   rebuild."
5. **Pull --rebase, push.** The shared-memory harness does NOT auto-push. A
   commit you don't push is invisible to everyone else.

## What the layering means on disk

```
sources/2026-08-26-scout.md        → "found ... torsion field thesis in Russian (URL)"
translations/2026-08-26-x-ru.md    → English translation of it (or chunk .en files)
database/research/...              → a structured record linking back to the source
database/persons/...               → the author, linked to the work
database/taxonomy/concepts.json    → the concept the thesis embodies (e.g. torsion)
```

Every layer points back to the layer below it. Nothing floats.