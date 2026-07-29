---
name: workflow-planner
description: Use para especificar e planejar trabalho persistente, selecionar workflow, risco, dependencias, skills, gates, paralelismo e contratos sem implementar tarefas.
---

# Workflow Planner

## Objetivo

Transformar grounding e especificacao em um plano auditado, um grafo de tarefas
com contratos integrais e o estado `planned`.

## Quando usar

- Nos estados `discussing`, `specified` ou em revisao explicita de plano.
- Para features, bugfixes amplos, backend ou mudancas de alto risco.
- Quando a execucao precisa sobreviver a outra sessao ou agente.

## Quando nao usar

- Para implementar uma tarefa.
- Para redesenhar silenciosamente um plano em execucao.
- Para promover um plano sem `plan-quality-checker`.

## Entradas esperadas

- `STATE.md`, roadmap, contexto, decisoes e requisitos.
- Spec da fase ou incertezas ainda abertas.
- Workflows, rubrics e skills existentes relevantes.

## Workflow

1. Use `project-context-loader` e persista grounding em `CONTEXT.md`.
2. Resolva ou registre incertezas; congele spec e criterios de aceite.
3. Selecione o workflow existente mais proximo e classifique o risco.
4. Use `execution-plan-builder` ou planner especializado para decompor tarefas.
5. Gere dependencias, gates, estrategia de paralelismo e politica de worktree.
6. Escreva o contrato integral de cada tarefa em `TASKS.md`.
7. Use `test-strategy-builder` para definir comandos e modo por tarefa.
8. Rode `plan-quality-checker`; corrija blockers e registre a evidencia.
9. Rode `framework-next seal-plan` com versao, decision ID e referencia da
   evidencia; isso sela `PLAN.md` + `TASKS.md`.
10. Solicite `specified → planned` somente depois do gate passar.

## Saida obrigatoria

- Spec e plano persistentes.
- Grafo de tarefas com contratos completos.
- Risco, skills, gates, testes, isolamento e rollback.
- Evidencia do plan gate.
- `STATE.md` pronto para `planned`, sem implementar tarefas.

## Criterios de aceite

- Cada tarefa e atomica, verificavel e possui contrato completo.
- Dependencias e arquivos paralelos nao conflitam.
- Plano alterado possui decisao e nova revisao.
- `planned` exige gate aprovado e risco classificado.

## Arquivos de apoio

- Protocolo: ../../kernel/protocol.md
- Politica de execucao: ../../kernel/execution-policy.md
- Plano: ../../templates/phase-plan.md
- Tarefas: ../../templates/phase-tasks.md
- Contrato: ../../templates/task-contract.md

## Exemplos de uso

- Codex: `$workflow-planner Planeje esta fase ate o estado planned.`
- Claude Code: `/workflow-planner Gere plano e contratos sem implementar.`
