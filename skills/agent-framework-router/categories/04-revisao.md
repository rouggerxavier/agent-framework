---
{
  "category": "revisao",
  "keywords": [
    "revis",
    "review",
    "diff\\b",
    "pr\\b",
    "pull request"
  ],
  "required": []
}
---

# Revisao

Instrucao: `fast`/`standard` usam uma review integrada; `critical` usa duas
independentes (spec antes de qualidade). Diff de agente inclui `agent-code-reviewer`.

| Situacao | Skill | Apoio |
|---|---|---|
| Revisar diff/PR | diff-reviewer | rubrics/diff-review, templates/audit-report |
| Decidir gate de code review | code-review-gate | templates/code-review-gate-report, agent-code-reviewer |
| Revisar conformidade com spec | spec-compliance-reviewer | templates/spec-compliance-review, workflows/review-application |
| Revisar qualidade depois da spec | code-quality-reviewer | diff-reviewer, workflows/review-application |
