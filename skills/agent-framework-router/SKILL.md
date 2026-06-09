---
name: agent-framework-router
description: Use primeiro para escolher quais skills, workflows, rubrics e templates do agent-framework aplicar a uma tarefa, sem planejar fases nem modelo.
---

# Agent Framework Router

## Objetivo
Dado um pedido, apontar rapidamente os assets certos do `~/agent-framework`. Dispatcher leve, nao executor.

## Quando usar
- No inicio, quando nao esta claro quais skills/rubrics/workflows usar.
- Para combinar poucos assets em tarefa pequena ou media.

## Quando nao usar
- Meta grande multi-fase: use `workflow-orchestrator`.
- Escolha de modelo/agente: use `model-routing`.
- Skill alvo ja obvia: chame-a direto.

## Workflow
1. Classifique a tarefa por intencao (tabela abaixo).
2. Liste 1-4 assets relevantes; corte o resto.
3. Se >1 fase ou >4 assets, encaminhe para `workflow-orchestrator` e pare.
4. Indique o primeiro asset a invocar.

## Prioridade alta
- Se o pedido mencionar brief, documentacao de feature/refatoracao, plano de execucao, organizar tarefa, quebrar em etapas ou preparar trabalho para outro agente, priorize `execution-plan-builder`.
- Se o pedido mencionar prompts por etapa, prompt para proximo agente, pacote de prompts ou delegar execucao, priorize `execution-prompt-builder`.
- Para esse fluxo, referencie `workflows/execution-brief` e mantenha o router como dispatcher.

## Tabela de roteamento
| Intencao | Skill | Apoio |
|---|---|---|
| Entrar em repo novo | project-context-loader, repo-map-builder | — |
| Ideias / objetivo aberto | brainstorm-lab | — |
| Brief/documentacao/plano de execucao | execution-plan-builder | workflows/execution-brief, brainstorm-lab, plan-quality-checker |
| Prompts por etapa para execucao | execution-prompt-builder | templates/execution-prompt-package, handoff-builder, code-review-gate |
| Criar/refatorar agente | agent-builder | workflows/agent-workflow, templates/agent-design |
| Auditar hardcode em agente | agent-anti-hardcode-auditor | templates/agent-hardcode-report, model-flexibility-auditor, config-surface-auditor |
| Auditar flexibilidade de modelo | model-flexibility-auditor | templates/model-flexibility-report, model-routing, runtime-qa-audit |
| Auditar configs/env/gitignore | config-surface-auditor | templates/config-surface-report, security-privacy-audit, docs-sync-auditor |
| Escolher peso da tarefa | task-mode-router | workflow-orchestrator, diff-reviewer, test-strategy-builder |
| Planejar backend em fatias | backend-slice-planner | templates/backend-slice-plan, api-contract-auditor, test-strategy-builder |
| Auditar plano antes de executar | plan-quality-checker | templates/plan-quality-report, rubrics/testing, rubrics/api-contract |
| Verificar cobertura do objetivo | goal-coverage-verifier | templates/goal-coverage-report, diff-reviewer, release-verifier |
| Empacotar release backend | backend-release-packager | templates/backend-release-package, release-verifier, goal-coverage-verifier |
| Decisao de arquitetura | architecture-decision | rubrics/architecture, templates/adr |
| Plano de implementacao | implementation-planner | templates/implementation-plan |
| Bug | bug-repro-lab | workflows/bugfix, rubrics/testing |
| Debug persistente | persistent-debug-session | templates/debug-session, bug-repro-lab, handoff-builder |
| Estrategia de testes | test-strategy-builder | rubrics/testing, templates/test-plan |
| Mapa de confianca de testes | test-confidence-mapper | templates/test-confidence-map, test-strategy-builder, release-verifier |
| Revisar diff/PR | diff-reviewer | rubrics/diff-review, templates/audit-report |
| Aplicar padroes locais antes de codar | coding-standards-enforcer | rubrics/coding-standards, repo-map-builder, diff-reviewer |
| Contrato de API | api-contract-auditor | rubrics/api-contract, workflows/api-refactor |
| Auditar dependencia | dependency-risk-auditor | templates/dependency-risk-report, security-privacy-audit, architecture-decision |
| Auditar migration/dados | data-migration-auditor | templates/data-migration-report, rubrics/data-migration, release-verifier |
| Sincronizar docs | docs-sync-auditor | templates/docs-sync-report, rubrics/docs-sync, release-verifier |
| Seguranca/privacidade | security-privacy-audit | rubrics/security-privacy |
| UI/UX | ui-ux-pro-max-audit | rubrics/ui-ux, workflows/frontend-refactor |
| QA app rodando | runtime-qa-audit | — |
| Release | release-verifier | workflows/release, templates/release-checklist |
| Handoff entre agentes | handoff-builder | workflows/agent-handoff, templates/handoff-summary |
| Conversa longa / contexto cheio | context-compressor | workflows/long-conversation-handoff |
| Refinar pedido cru | prompt-refiner | templates/prompt-package |
| Refinar prompt por acao | prompt-refiner | templates/action-prompt-package |
| Refinar prompt de agente | agent-prompt-refiner | templates/action-prompt-package, agent-builder, agent-anti-hardcode-auditor |
| Desenhar tool de agente | agent-tool-designer | templates/agent-tool-design, agent-builder, security-privacy-audit |
| Auditar contrato de tool | tool-contract-auditor | templates/tool-contract-report, api-contract-auditor, security-privacy-audit |
| Validar tool em runtime | tool-runtime-validator | templates/tool-runtime-validation, runtime-qa-audit, test-confidence-mapper |
| Implementar guardrails de agente | agent-guardrails-implementer | templates/agent-guardrails-plan, agent-security-auditor, tool-contract-auditor |
| Auditar seguranca de agente | agent-security-auditor | templates/agent-security-report, security-privacy-audit, env-gitignore-auditor |
| Auditar env/gitignore/secrets | env-gitignore-auditor | templates/env-gitignore-report, config-surface-auditor, docs-sync-auditor |
| QA runtime de agente | agent-runtime-qa | templates/agent-runtime-qa-report, runtime-qa-audit, tool-runtime-validator |
| Planejar evals de agente | agent-eval-planner | templates/agent-eval-plan, test-strategy-builder, test-confidence-mapper |
| Auditar observabilidade de agente | agent-observability-auditor | templates/agent-observability-report, persistent-debug-session, agent-security-auditor |
| Planejar logs de feature | feature-logging-planner | templates/feature-logging-plan, runtime-qa-audit, security-privacy-audit |
| Decidir gate de code review | code-review-gate | templates/code-review-gate-report, diff-reviewer, agent-code-reviewer |
| Revisar codigo de agente | agent-code-reviewer | templates/agent-code-review-report, tool-contract-auditor, agent-security-auditor |
| Decidir git/commit/PR | git-decision-router | templates/git-decision-report, commit-readiness-checker, pr-description-builder |
| Checar commit readiness | commit-readiness-checker | templates/commit-readiness-report, docs-sync-auditor, env-gitignore-auditor |
| Montar descricao de PR | pr-description-builder | templates/pr-description, backend-release-packager, goal-coverage-verifier |
| Decidir documentacao | documentation-decision-router | templates/documentation-decision, architecture-decision, docs-sync-auditor |
| Documentar agente | agent-doc-writer | templates/agent-doc, templates/agent-design, docs-sync-auditor |
| Mapear deadcode/orfaos | deadcode-orphan-mapper | templates/deadcode-orphan-map, repo-map-builder, test-confidence-mapper |
| Otimizar agente | agent-optimization-auditor | templates/agent-optimization-report, model-routing, agent-runtime-qa |
| Auditar performance budget | performance-budget-auditor | templates/performance-budget-report, rubrics/performance-budget, runtime-qa-audit |
| Instalar/atualizar framework | agent-framework-installer | docs/portability, docs/maintenance |
| Evoluir framework por recorrencia | skill-evolution-loop | docs/task-memory, docs/skill-standards |
| Auditar qualidade de skill | skill-quality-auditor | docs/skill-standards, installers/verify-framework |

## Saida obrigatoria
- Intencao detectada.
- Assets selecionados (skill + apoio).
- Primeiro asset a invocar, ou encaminhamento para `workflow-orchestrator`.

## Criterios de aceite
- No maximo 4 assets; sem listar tudo.
- Nao duplicar checklist de rubric/workflow aqui; so referenciar.
- Encaminhar metas grandes em vez de planejar fases.

## Exemplos de uso
- Codex: `$agent-framework-router Qual skill para auditar este PR de API?`
- Claude Code: `/agent-framework-router Por onde começo neste repo desconhecido?`
