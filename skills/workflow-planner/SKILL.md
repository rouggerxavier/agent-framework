---
name: workflow-planner
description: Use para plano curto em standard ou planejamento persistente completo em critical; nao e obrigatorio em fast.
---

# Workflow Planner

## Objetivo

Produzir planejamento proporcional ao modo: curto e executavel em `standard`, ou
auditado/persistente com contratos integrais em `critical`.

## Quando usar

- Em `standard`, para duas a cinco etapas dependentes ou risco moderado.
- Em `critical`, nos estados `discussing`, `specified` ou revisao de plano.
- Quando ha valor concreto em planejar; nunca apenas por quantidade de arquivos.

## Quando nao usar

- Para implementar uma tarefa.
- Em `fast`; inspecione e implemente diretamente.
- Para redesenhar silenciosamente um plano em execucao.
- Para exigir plan gate em `standard`.

## Entradas esperadas

- Objetivo, modo selecionado e contexto focado.
- Em `critical`: `STATE.md`, roadmap, spec, decisoes e requisitos.
- Workflows, rubrics e skills existentes relevantes.

## Workflow

1. Confirme `mode`.
2. Em `standard`, use contexto ja lido, escreva um plano curto com objetivo,
   2-5 passos, arquivos/areas, verificacao e riscos conhecidos.
3. Em `standard`, crie `.agent/STATE.md` e `.agent/PLAN.md` somente se atravessar
   sessoes, houver tarefas dependentes ou o usuario pedir persistencia. Nao crie
   roadmap, contratos, seal ou ledger automaticamente.
4. Em `critical`, execute o workflow P0/P1 completo: grounding persistente,
   spec, workflow, grafo, contratos, testes, isolamento e rollback.
5. Somente em `critical`, rode `plan-quality-checker`, registre evidencia, use
   `framework-next seal-plan` e solicite `specified → planned`.

## Saida obrigatoria

- `standard`: plano curto, verificacao proporcional e persistencia justificada ou
  explicitamente dispensada.
- `critical`: spec/plano persistentes, contratos completos, gates, evidencia e
  `STATE.md` pronto para `planned`.

## Criterios de aceite

- `standard` nao recebe plan seal, ledger completo ou contrato formal por default.
- `critical` preserva atomicidade, contratos, dependencias, plan gate e seal.
- `fast` nao depende desta skill.

## Arquivos de apoio

- Protocolo: ../../kernel/protocol.md
- Politica de execucao: ../../kernel/execution-policy.md
- Plano: ../../templates/phase-plan.md
- Tarefas: ../../templates/phase-tasks.md
- Contrato: ../../templates/task-contract.md

## Exemplos de uso

- Codex: `$workflow-planner Planeje esta fase ate o estado planned.`
- Claude Code: `/workflow-planner Gere plano e contratos sem implementar.`
