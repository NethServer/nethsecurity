---
name: create-issue
description: Turn messy raw material — coworker chat excerpts, support discussions, log snippets, debugging findings, CI failures — into a well-formed GitHub issue on the NethServer/nethsecurity tracker via the gh CLI. Use whenever the user asks to "open an issue", "file a bug", "create a feature request", "report this upstream", or pastes a conversation/log and wants it tracked as an issue, even if they don't say "issue" explicitly (e.g. "we should track this", "make a ticket for this").
---

# Create Issue

Turn unstructured input (chats, logs, findings) into a GitHub issue on **NethServer/nethsecurity**, following the [NethServer handbook](https://github.com/NethServer/dev/blob/master/handbook/issues.md).

The input is usually messy: Italian/English coworker chats, partial logs, half-formed conclusions. Your job is extraction and structuring — not invention. If a template section has no supporting evidence in the input, ask the user or mark it clearly rather than fabricating plausible details. A wrong "steps to reproduce" is worse than an honest gap: QA will follow those steps verbatim.

**The tracker is always `NethServer/nethsecurity`** — including issues whose fix lands in another repo (`nethsecurity-ui`, `nethsecurity-controller`, `nethsecurity-monitoring`). Don't propose those repos as the target and don't ask which one to use. The only exception is the user naming a different tracker explicitly (see Overrides).

## Who the issue is written for

An issue is read by product people, QA and support — not only by whoever will write the patch. So the **title and body stay user-facing**: the visible symptom, who it hits, why it matters. Keep out of the body prose: method names, file paths, function/interceptor-level mechanics, config keys, and recaps of a diff. Package names and versions are fine (they belong in **Components** / **Additional context**), and logs and commands are fine under **Steps to reproduce** where QA needs them verbatim.

The title carries the same register as the body — `Standalone UI shows duplicate error messages`, not `UI: Suppress global error toast in standalone mode`. A component prefix is optional and fine when it aids scanning (`Dashboard: …`, `rsyslog: …`).

The technical analysis you gathered while investigating is not wasted, but it does not go in the body silently and it does not get posted silently either. Print it in chat as a clearly separate block and ask the user what they want done with it: posted as a comment on the issue, kept for the PR description, or dropped. Posting it is a GitHub write — it needs its own go-ahead (see step 4).

## Workflow

### 1. Extract

From the provided material, identify:

- **Problem or request** — one sentence, in user-facing terms. This drives the title.
- **Type** — the repo's native GitHub issue type (not a label). Bug (defect needing resolution) or Feature (improvement/new functionality) cover most cases; the repo also defines Task, Design, Backend, Frontend, Draft. When ambiguous ("X is annoying"), ask. Verify the exact name exists before filing: `gh api repos/NethServer/nethsecurity/issue-types --jq '.[].name'`.
- **Component and version** — affected `ns-*` package or component name(s) and version, e.g. `ns-flashstart 1.0.5`, `nethsecurity-ui 2.23.2`. Package name only — never file paths or function names. Image version goes here too when known (`Image version: 8-23.05.5-ns.1.3.0`), but don't block on it: if there's no live device to check, omit the image version line rather than guessing. Package versions come from `apk list ns-\* | sort` on the device, the package's `Makefile` `PKG_VERSION` when working from source, or `package.json` / the `ns-ui` Makefile for the UI. Chats often mention this in passing; logs often contain version strings.
- **Reproduction evidence** — commands, config, sequence of events (bugs only).
- **Expected vs actual behavior** (bugs only).
- **System output** — relevant log lines, error messages. Trim to the meaningful part.
- **Links** — community.nethserver.org threads, external docs the user provided. Not the PR/commit that will fix or implement this — an issue is normally filed before that work exists, and even when it doesn't (tracking already-drafted work), that link belongs in the Development section (step 5), never as prose in the body.

Sanitize before drafting: strip hostnames, public IPs, usernames, tokens, customer names from any pasted logs or chat. Replace with placeholders like `<hostname>`, `<wan-ip>`.

If the source chat is not in English, translate the substance — issues are written in English.

### 2. Check for duplicates

Search before drafting:

```bash
gh issue list -R NethServer/nethsecurity --search "<keywords>" --state all --limit 10
```

Try 2–3 keyword variants (component name, error message fragment, feature noun). If a likely duplicate exists, show it to the user and ask whether to comment on the existing issue instead of opening a new one.

### 3. Draft

Title: concise and user-facing, matching the style of recent issues (e.g. `Standalone UI shows duplicate error messages`, `rsyslog: Root filesystem fills up`). No `[Bug]`/`[Feature]` prefixes — the type is set separately.

Body: use the matching template below. **Drop a section header entirely if it has nothing to hold** — don't emit "Alternative solutions" with "None surfaced". Only fall back to `Unknown — <what's missing>` for a section the reader actually needs and the input just doesn't cover (e.g. steps to reproduce on a bug) — that's a gap worth flagging, not a section worth deleting.

**Bug template:**

```markdown
**Steps to reproduce**

- Step one
- Step two

**Expected behavior**

What should happen.

**Actual behavior**

What happens instead.

**Components**

Image version: 8-x.y.z-ns.a.b.c (omit if unknown)
Affected package/component name(s) and version — name only, no file paths.
```

**Feature template:**

```markdown
Opening paragraph: WHY this is being asked and the PURPOSE of the feature, in user-facing terms. No "Brief description:" label — the paragraph stands on its own.

**Proposed solution**

What should be adopted, described by behavior rather than by implementation.

**Alternative solutions**

Alternatives considered, if any surfaced in the discussion. Omit the header entirely if none did.

**Additional context**

Affected package/component name(s) and version, one per line (e.g. `nethsecurity-ui 2.23.2`), plus any community-thread or doc URLs the user supplied. Nothing else: no list of files to change, no packages-to-touch plan, no implementation notes — that belongs in the PR, not the issue.
```

Neither template carries a "See also" for the implementing PR/issue — that link is added post-creation via GitHub's Development section (step 5), never as a body URL.

Presentation matters (per handbook): use code fences for logs and commands, lists for steps, bold for section headers exactly as in the templates.

### 4. Show the draft, then get go-ahead

**Showing the draft means printing, in chat: the title, the complete body, the type, the milestone and the assignee.** Printing the `gh` command instead of the body is not showing the draft. Neither is describing what the body says.

Fields first, permission second — they are separate exchanges:

1. Resolve the field candidates: `gh api repos/NethServer/nethsecurity/milestones --jq '.[].title'` and `gh api user --jq '.login'`. Ask milestone and assignee in one question, offering the nearest open milestone and the user's own login as the suggested answers (both may legitimately be "none"). Ask about type here too if it was ambiguous in step 1.
2. Re-show the corrected draft in full, then ask separately whether to file it.

**Never write to GitHub without explicit confirmation for that specific write.** This gate covers every write: `gh issue create`, `gh issue edit`, `gh issue comment`, `gh pr edit`, and any label/milestone/assignee change. Permission to file is not permission to then edit, comment, or touch a PR — each one is asked for on its own. Issues are public and notify subscribers.

Explicit confirmation means the user affirmatively said to go (e.g. "yes", "go ahead", "file it", "looks good, send it"). It does NOT include: answering a field question (repo, assignee, milestone, type), correcting a detail in the draft, or any other reply that only narrows or fixes the draft. **Never bundle a field question and the file/no-file question together** — a single `AskUserQuestion` mixing "which repo?" with "file now?" has already caused an issue to be filed against the user's wishes. Treat "show it to me" / "present it to me" literally: showing is the deliverable, full stop. When in doubt about whether a reply counts as go-ahead, it doesn't — ask.

### 5. Iterating on the draft

When the user wants to review or hand-edit the draft across turns, iterate **in plan mode using the harness plan file** (`~/.claude/plans/<name>.md`) — that is the mechanism the user works in.

Never write draft files into the repo working tree; a draft dropped in the repo root has been explicitly rejected. Scratchpad files are only for the `--body-file` payload at filing time.

### 6. File

```bash
gh issue create -R NethServer/nethsecurity \
  --title "<title>" \
  --body-file <draft.md> \
  --type "<type>" \
  --assignee "<gh-login>" \
  --milestone "<milestone>"
```

Write the body to a temp file (scratchpad) and use `--body-file` — inline `--body` mangles backticks and newlines.

`--type` is required every time (verified against the list from step 1, not guessed). `--assignee` takes a GH login, not a display name — resolve it with `gh api user --jq '.login'` for "assign it to me". `--milestone` takes the exact title as verified in step 4; don't create one on the fly. Drop either flag when the answer in step 4 was "none".

Labels: apply only labels that exist on the repo (`gh label list -R NethServer/nethsecurity`). Currently meaningful at creation time: `controller` (controller-related issues). Do NOT apply workflow labels (`testing`, `verified`, `needs image`, `milestone goal`) — those belong to the dev/QA/release cycle.

**Linking an existing PR (Development section):** if a PR already implements this issue (tracking already-drafted work, rather than the usual issue-before-code order), link it after the issue is filed rather than pasting its URL in the body — GitHub only surfaces a PR in the issue's Development sidebar when the PR body contains a closing keyword. Confirm you (or the requesting user) authored the PR before editing its description (`gh pr view <n> --json author`), then **append** the closing keyword, preserving the existing body:

```bash
BODY=$(gh pr view <n> -R <repo> --json body -q .body)
gh pr edit <n> -R <repo> --body "${BODY}

Closes #<issue-number>"
```

Use `Closes OWNER/REPO#<issue-number>` when the PR lives in another repo (e.g. `nethsecurity-ui`). Never pass `--body "Closes #N"` alone — that replaces the whole PR description. This linking is a separate GitHub write: ask for it separately (step 4). It also auto-closes the issue when the PR merges, which is the desired outcome for a tracking issue.

After creation, report the issue URL.

## Overrides

- Different repo: the user can name another tracker explicitly (e.g. `NethServer/dev` for NethServer/NethVoice topics) — pass a different `-R` and search for duplicates there instead. Never infer the tracker from where the code lives.
- Multiple issues in one input: propose the split first, then draft each separately.

## Keeping this skill current

When the user corrects a convention used here mid-task (a template section that shouldn't have been there, a field that should always be set, a linking convention, the register of the body), update this file in the same turn rather than only fixing the immediate draft.

Re-read the whole file first, then edit the specific section the correction applies to — and delete or rewrite any other rule the correction now contradicts. Appending a new caveat next to a stale one has already left this file self-contradictory for a week; a correction is not applied until nothing in the file still says the old thing.
