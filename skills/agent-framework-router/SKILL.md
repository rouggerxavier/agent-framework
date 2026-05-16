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

## Tabela de roteamento
| Intencao | Skill | Apoio |
|---|---|---|
| Entrar em repo novo | project-context-loader, repo-map-builder | — |
| Ideias / objetivo aberto | brainstorm-lab | — |
| Decisao de arquitetura | architecture-decision | rubrics/architecture, templates/adr |
| Plano de implementacao | implementation-planner | templates/implementation-plan |
| Bug | bug-repro-lab | workflows/bugfix, rubrics/testing |
| Estrategia de testes | test-strategy-builder | rubrics/testing, templates/test-plan |
| Revisar diff/PR | diff-reviewer | rubrics/diff-review, templates/audit-report |
| Contrato de API | api-contract-auditor | rubrics/api-contract, workflows/api-refactor |
| Seguranca/privacidade | security-privacy-audit | rubrics/security-privacy |
| UI/UX | ui-ux-pro-max-audit | rubrics/ui-ux, workflows/frontend-refactor |
| QA app rodando | runtime-qa-audit | — |
| Release | release-verifier | workflows/release, templates/release-checklist |
| Handoff entre agentes | handoff-builder | workflows/agent-handoff, templates/handoff-summary |
| Conversa longa / contexto cheio | context-compressor | workflows/long-conversation-handoff |
| Refinar pedido cru | prompt-refiner | templates/prompt-package |
| Instalar/atualizar framework | agent-framework-installer | docs/portability, docs/maintenance |

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
