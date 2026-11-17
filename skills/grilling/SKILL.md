---
name: grilling
description: Use to stress-test a plan, decision, or idea through relentless round-based interview until shared understanding; triggers "grill", "question my plan", "stress-test my thinking".
---

# Grilling

## Objective
Reach shared understanding of a plan, decision, or idea by asking questions in
rounds, without assuming answers the user has not given.

## When to use
- User wants to test a plan, decision, or idea before acting.
- Triggers: "grill", "question my plan", "stress-test", "interview my plan".

## When not to use
- Request is already clear and executable: execute it.
- Open exploration of alternatives: use `brainstorm-lab`.
- Quality check of a finished plan: use `plan-quality-checker`.
- Decision with several valid paths to classify by owner: use `decision-authority-router`.

## Expected inputs
- Plan, decision, or idea as text, or a file that describes it.

## Workflow
1. Map the idea as a **decision tree**: each decision branches into the decisions that depend on it.
2. Compute the **frontier**: decisions whose prerequisites are already settled.
   Questions that depend on an answer still open wait for a later round.
3. Ask the whole frontier in one round. Number each question and give your recommended answer.
4. Format each question so that "yes" accepts your recommendation:

   ```
   ❓ **Q1** - **<title>**: <question body, with options if any>

   ➡️ <recommended answer>
   ```

5. Stop and wait for the user's answers.
6. Recompute the frontier with the answers and repeat.
7. End when the frontier is empty: every branch visited, nothing assumed silently.
8. Facts about the environment (files, tools, code) are your job: look them up
   before asking. Decisions belong to the user: ask.

## Required output
- Question rounds in the format above, or at the end, a summary of the shared
  understanding: decisions taken and open items.

## Acceptance criteria
- No question depends on an answer not yet given.
- Every question has a recommendation.
- Verifiable facts were looked up, not asked.
- No action is taken before the user confirms the understanding.

## Usage example
- "grill my plan to move auth to JWT" -> round 1 asks the frontier decisions
  (storage, expiry, revocation), each with a recommendation.

Origin: adapted from `mattpocock/skills` (MIT license).
