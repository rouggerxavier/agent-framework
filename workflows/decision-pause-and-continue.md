# Decision Pause and Continue Workflow

Use when a multi-agent worker discovers a choice classified as
`user_required`.

## Principle

A pending user decision blocks the dependent work, not the whole project.

## Sequence

1. Stop the affected worker before it guesses.
2. Create a `Q-###` entry in `.agent/notes/QUESTIONS.md`.
3. Record:
   - the exact question;
   - context and options;
   - recommendation when useful;
   - task/dispatch/phase affected;
   - what is blocked;
   - what independent work may continue.
4. Mark the dispatch `awaiting_decision`.
5. Mark dependent dispatches/tasks as waiting on the same question ID.
6. Put the question ID in `ORCHESTRATION.md.awaiting_user`.
7. Refresh `.agent/notes/INDEX.md`.
8. Re-run scheduling:
   - start any eligible task from the same phase that does not depend on the
     question;
   - if that phase has no independent work, prepare another already-approved
     spec/phase whose dependencies are satisfied;
   - do not invent a new product direction just to stay busy.
9. Ask the user the recorded question without losing the rest of the queue.
10. When answered:
    - update `QUESTIONS.md`;
    - write the formal decision to `DECISIONS.md`;
    - revise affected spec/plan/dispatches;
    - unblock dependent work;
    - schedule it when a lane becomes available.

## Constraints

- Never continue through a decision dependency by assumption.
- Never freeze unrelated lanes merely because one question is open.
- A later phase may proceed only when its own prerequisites and product intent
  are already approved.
- Integration order must still respect dependencies.
