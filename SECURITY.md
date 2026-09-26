# Security — the rules that keep this from becoming a liability

Same shape as the house rules: every one of these is something we got wrong first.

## The one principle

**Assume every public surface leaks until you have proven otherwise — and prove it against the rendered output, not your source files.** The source is what you intended. The render is what shipped. Grep the render.

---

## 1. Secrets

- A secret is anything that grants access: API keys, tokens, passwords, private keys, connection strings, and any file containing them.
- **Secrets never go in a repo, a prompt, a chat message, or a memory block.** They live in your platform's secrets store and get referenced by name (`$MY_KEY`).
- If a secret ever lands in a repo or a chat, treat it as compromised and rotate it. **Deleting the message is not rotating.**
- **Your sandbox may write your key in cleartext into `<shared-repo>/.git/config`.** It isn't committed, but anything with shell access on that machine can read it. Treat that file as containing a key.
- **Watch your encodings.** Writing a config file as UTF-8 *with* a byte-order mark makes some CLI parsers echo the whole file to stderr. The secret ends up in a log. Write UTF-8 with **no BOM**, and delete any log that captured environment contents.
- **Rotate keys you created. Do not revoke keys the platform injected.** And track fingerprints, not names — names get reused, and they lie.

## 2. Access — the keys model

- **One key per person. One key per agent.** Never a shared login, never a shared password, never "here's the link."
- Prefer **collaborator invites on a private repo** over any password gate. Invites are per-person and individually revocable, which is the entire point.
- **Start everyone at the lowest tier that works.** Raise on demonstrated need, not on politeness.
- **Know the scoping trap.** On GitHub, a fine-grained token's *Repository Access* list is separate from its *Permissions*. A token scoped to one repo will 404 on every other repo, and it looks exactly like a broken permission.
- **Write down who has access, and review it.** Access granted in September is still access in March.
- **Remember what shared memory cannot do.** A shared repo has **no per-file access control**. Attaching it to an agent gives that agent everything in it. There is no partial attach, so "give them access to part of it" is not an option — build a separate intake instead.

## 3. The private / public boundary

The rule that matters most the moment you have two of anything.

- **Publication must be an allowlist, never a glob.** Copying "these three named folders" is safe. Scanning "everything under this directory" is not. An allowlist that fails shows up as a file silently **missing** — visible, benign. A glob that fails shows up as a file silently **published** — invisible, harmful.
- **An allowlist that is the only thing between private and public is a tripwire.** Say so in a comment, so the next person who edits it knows what they are holding.
- **Two directories with the same name are not the same thing.** A folder called `synthesis/` in your private repo and a folder called `synthesis/` on your public site are unrelated. Never reason about privacy from a folder name.
- **A path check is not a publication check.** We verified a folder returned 404 and concluded its contents were private. The contents were rendering on a *different* public page. If you want to know whether something is private, check where the **content** renders, not whether the address resolves.
- Decide your lanes once, write them down, and put a human decision at the boundary.

## 4. Label provenance on the artifact

If you mirror someone else's document, the page itself must say whose claim it is. One line: *"mirrored third-party document; the claims are the source author's, not ours."*

That line is the difference between an archive and a rumor mill. It is also your legal footing, because fair use reads very differently on a labeled mirror than on an unlabeled one.

## 5. Verify, because checks lie

- **A check that cannot fail cannot detect anything.** If your monitor reads its threshold from the same file it monitors, it will always pass. Prove your check *can* fail before you trust it when it passes.
- **An operation built never to fail cannot detect being pointed at the wrong thing.** We had a push that was structurally incapable of being rejected. It succeeded beautifully while pushing the wrong source. When a design removes a failure mode, ask which failure it removed the ability to **detect**.
- **Silent success and silent failure look identical.** Log check-ins, not intentions. An agent that says it did something and an agent that did it read the same in a transcript. **Never wrap a critical step in a bare `except: pass`.**

## 6. Git safety on a published branch

- **Count your files before you commit to a live branch.** Our public vault is around 45,000 tracked files. Under about a thousand means your checkout is broken — stop, re-clone, do not commit.
- **Never force-push a published branch.** We emptied a public vault for two hours doing exactly that. If a push is rejected, re-pull and retry.
- **Write down why.** Any change of state should carry its reason, logged when it happens.

## 7. Audit yourself

Run a weekly adversarial pass against your own system and let it **report only**. Check: committed credentials, unexpected network listeners, file permissions, and prompt-injection surface in your agent configs. An auditor that can act is a second liability.

---

## The short version

Assume the render leaks. Allowlist, never glob. One key per person. Never commit a secret. Path checks are not publication checks. Label whose claim it is. Count your files. Never swallow an error. And make your checks capable of failing.
