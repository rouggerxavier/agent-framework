---
{
  "category": "software",
  "keywords": [
    "feature",
    "endpoint",
    "bug",
    "refator",
    "backend",
    "api\\b",
    "implement",
    "corrij",
    "debug",
    "plano de",
    "brief",
    "repo novo",
    "ideia"
  ],
  "required": []
}
---

# Desenvolvimento de software

Instrucao: menor mudanca completa; reuse helpers e padroes do repo antes de criar
abstracao. Planejamento so na medida do modo. Se o pedido mencionar brief, plano de
execucao, quebrar em etapas ou preparar trabalho para outro agente, priorize
`execution-plan-builder` (`workflows/execution-brief`); prompts por etapa ou
delegacao, `execution-prompt-builder`.

| Situacao | Skill | Apoio |
|---|---|---|
| Entrar em repo novo | project-context-loader, repo-map-builder | — |
| Ideias / objetivo aberto | brainstorm-lab | grilling |
| Testar a fundo um plano ou decisao ja formada | grilling | brainstorm-lab |
| Brief/documentacao/plano de execucao | execution-plan-builder | workflows/execution-brief, plan-quality-checker |
| Prompts por etapa para execucao | execution-prompt-builder | templates/execution-prompt-package, handoff-builder, code-review-gate |
| Refinar pedido cru ou prompt por acao | prompt-refiner | templates/prompt-package, templates/action-prompt-package |
| Plano de implementacao | implementation-planner | templates/implementation-plan |
| Planejar backend em fatias | backend-slice-planner | templates/backend-slice-plan, api-contract-auditor, test-strategy-builder |
| Auditar plano antes de executar | plan-quality-checker | templates/plan-quality-report, rubrics/testing, rubrics/api-contract |
| Decisao de arquitetura | architecture-decision | rubrics/architecture, templates/adr |
| Aplicar padroes locais antes de codar | coding-standards-enforcer | rubrics/coding-standards, repo-map-builder |
| Contrato de API | api-contract-auditor | rubrics/api-contract, workflows/api-refactor |
| Bug | bug-repro-lab | workflows/bugfix, rubrics/testing |
| Debug persistente | persistent-debug-session | templates/debug-session, bug-repro-lab, handoff-builder |
| Mapear deadcode/orfaos | deadcode-orphan-mapper | templates/deadcode-orphan-map, repo-map-builder |
