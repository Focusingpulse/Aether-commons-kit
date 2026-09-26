# Boundaries — what may leave the house

This is the most important file in the kit and the one most likely to be skipped, because
nothing goes wrong the day you skip it. It goes wrong a year later, and by then the problem
cannot be undone.

**Write your policy before you have something to publish.** A boundary decided in advance
is a policy. A boundary decided at the moment of maximum excitement is a gamble.

---

## The three tiers

Copy the shape. The *categories* below are the ones that recur; your specific paths and
decisions are yours.

### TIER 0 — never publish

Material that must not become public without a deliberate, recorded decision.

Typical residents: third-party book files and scraped artifacts at reproduction scale ·
extracted text from copyrighted works · your own analytical claims about named people and
institutions · your own legal/exposure analysis · raw harvested reference data · internal
indexes · internal ops queues.

### TIER 1 — review before publish

Material that could be published but crosses a line requiring a human decision.

| Class | Why it needs a human |
|---|---|
| Any full-text reproduction of a third-party work | Reproduction and distribution. No preservation exception covers *publishing*. |
| Any health or medical claim, however framed | Regulated-claims regime, separate from copyright entirely |
| Any negative factual claim about an identifiable **living** person | Defamation. Note the burden can reverse outside the US. |
| Declassified material naming a third country | National-security exposure, not a copyright question |
| A trademark used in a way that implies endorsement | Trademark |

### TIER 2 — publish freely

Metadata and facts (facts are not copyrightable) · short quotations with attribution ·
your own authored registers and indexes · your analysis of *ideas* · links out to where a
work legitimately lives · public domain material · permissioned material.

---

## Three rules that outrank everything else in this file

**1. Verify the boundary by rendering, not by path.**
Checking that a source path returns 404 tells you nothing about whether the content is
published. A build script can render a private artifact's content onto a public page while
its own path 404s. **Any tier verification must check the rendered output.** We verified by
path, believed the tier was holding, and it was not.

**2. Removal stops future exposure. It does not undo publication.**
Anything already fetched stays fetched — search caches, archives, RSS, scrapers, and
anyone's copy. Which means the boundary is far cheaper to hold *before* publishing than to
rebuild afterward. This is the entire argument for having a policy early.

**3. If you remove something, log the reason at the moment you remove it.**
A documented reason is defensible. A silent deletion is not — and in a defamation context,
a quiet removal can read as consciousness of liability. Record what, when, and why.

---

## The intake lane — how to let people contribute without opening the library

The moment someone wants to contribute, you have two options and only one of them works.

**Do not attach the library.** A shared repo has **no per-file access control**. Attaching
it gives every attached agent everything in it, including the tiers that exist so that
nobody reads them. There is no partial setting, and no permission grant can create one.

Also: if outsiders can write in, nobody can enforce the tiers. An unenforced policy is
worse than no policy, because it documents that you knew.

**Build an intake lane instead.**

| | Public | Curated private | Intake |
|---|---|---|---|
| Where | your public site | per-member gated repos | a submission area, theirs to fill |
| Read | everything | packs chosen for them | their own submissions |
| Write | nothing | nothing | anything they want to propose |

Submissions are screened for **rights, tier, and provenance**. Cleared material is
*ingested* by you — with the contributor's name on the provenance line — and the rest is
declined with a stated reason.

**The framing that makes this honest rather than stingy:** *we preserve, we do not
redistribute.* An archive that accepts everything from everyone is not an archive, it is a
drop box — and the drop box is the thing that gets taken down. The contributor loses
nothing but the credit they were going to get anyway.

---

## The risk register

Keep one. One row per live exposure, with an owner and a decision date. It is the only
artifact that stops a known problem from becoming an unknown one.

| Risk | Tier | Status | Owner | Decision |
|---|---|---|---|---|
| _what_ | _0/1_ | open / resolved / latent | _name_ | _date_ |

**Order it by whether it is live, not by how alarming it sounds.** We ranked defamation
high and copyright low until an actual audit showed the reverse: the copyright item was
live and the defamation item was mostly deceased institutions and careful attribution. The
alarming thing was the safe thing, and the boring thing was the live one.
