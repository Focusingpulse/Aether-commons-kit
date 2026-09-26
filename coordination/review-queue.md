# The review queue

The rule: **nobody ships their own work.**

This is the coordination mechanism everyone skips and everyone regrets. It costs one extra
step and it catches the class of error that no amount of care in a single pass ever catches,
because the person who made the mistake is the worst possible reviewer of it.

---

## The shape

Four roles, one file:

| Step | Who | What happens |
|---|---|---|
| **Submit** | Producer | Hands the artifact in with what it is and where it goes |
| **Claim** | Reviewer | A *different* member takes it |
| **Resolve** | Reviewer | Returns a verdict: accepted, or rejected with findings |
| **Fix** | Producer | Applies the findings. The reviewer never edits the artifact. |

**Three hard rules:**

1. **No self-review.** The submit step must reject a submission where producer equals
   reviewer. Enforce it in the tooling, not in a convention — a rule that depends on
   everyone remembering is not a rule.
2. **The reviewer is read-only.** Findings go back to the producer to fix. The moment a
   reviewer can edit, the artifact has two authors and neither is accountable.
3. **No publish without an explicit verdict.** "Looks fine" is not a verdict. Accepted or
   rejected with findings. Anything else is silence wearing the costume of approval.

---

## Two lenses, and when you need both

Run every artifact past whichever lenses apply. They catch different failures.

**Identity lens** — is this factually *ours and correct*?
- Names spelled exactly as they are canonically known, everywhere
- Geography and scope accurate, nothing outside the declared boundary added
- No fabricated facts, metrics, IDs, or quotes
- Any structured data describes the thing it is attached to

**Voice lens** — does this sound like the person it is coming from?
- Read it aloud. Would they say this?
- No generic filler, no inflated vocabulary, no rhythmic padding
- Concrete over abstract; specifics over claims
- Publish-ready, not draft-ready

**Anything going public needs both.** Anything with structured data needs both. A change to
a private internal file needs one, or none — the point is to match the ceremony to the
consequence, or people will route around the queue to avoid the ceremony.

---

## What this does not fix

The queue is architecture. Participation is discipline. A review gate that nobody uses is
worse than no gate, because it produces a record of approvals that were never made.

So: keep it cheap enough that people use it. If a submission takes longer than the work it
reviews, the queue will be bypassed. One line in, one verdict out.

## Start with one artifact type

Do not put the whole family behind the queue on day one. Pick the one artifact type where a
mistake is expensive — the thing that goes public — and gate only that. Expand when the
habit exists.
