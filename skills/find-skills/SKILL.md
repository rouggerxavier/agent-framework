---
name: find-skills
description: Use to find an existing skill before creating a new one, local first, then the external ecosystem ("is there a skill for X", "how do I do X", "find a skill").
---

# Find Skills

## Objective
Find a skill that already solves the request, local first, then in the external
ecosystem. Install nothing without explicit approval.

## When to use
- User asks "is there a skill for X", "how do I do X", or asks for a new capability.
- Before creating a new skill, to avoid duplicates.

## When not to use
- Target skill is obvious: call it directly.
- Creating a skill from scratch: use `skill-scout` (local, marketplace, GitHub search) or
  `skill-evolution-loop` when a pattern repeats.
- Installing the framework itself: use `agent-framework-installer`.

## Expected inputs
- What the user wants to do, as keywords.

## Workflow
1. Identify domain and task (e.g. react performance, pr review, changelog).
2. Search local: `ls skills/` and `grep -l -i "<term>" skills/*/SKILL.md`.
   If a local skill covers it, stop and point to it.
3. If nothing local fits, search external: `npx skills find <terms>`
   (optional `--owner <owner>`). Also check https://skills.sh/.
4. Verify before recommending. Never recommend from search results alone:
   - Installs: prefer 1K+; be cautious below 100.
   - Source: official sources (`vercel-labs`, `anthropics`, `microsoft`) weigh more.
   - Repo stars: below 100, treat with skepticism.
   - License and content: read the `SKILL.md` before adopting.
5. Present to the user: name, what it does, installs, source, install command, skills.sh link.
6. Install only if the user says yes. Use `npx skills add <owner/repo@skill>`
   without `-y` by default. After approval, install and run `bash installers/verify-framework.sh`.
7. Nothing found: say so, offer to solve directly, and suggest creating a skill via `skill-scout`.

## Required output
- Candidate list (local and external), each with source, verification done, and
  install command, or a statement that nothing was found.

## Acceptance criteria
- Local search ran before external search.
- Each recommendation has source and verification (installs, stars, license).
- No installation without explicit user "yes".

## Usage examples
- "is there a skill for PR review?" -> `ls skills/` finds `diff-reviewer` and
  `code-review-gate`; no external search.
- "is there a skill for docker deploy?" -> nothing local; run `npx skills find docker deploy`,
  then present with verification.

Origin: adapted from `vercel-labs/skills` (MIT license).
