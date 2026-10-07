---
name: workflow-orchestrator
description: Roteia chamadas legadas ao planner/runner e, quando houver equipe multiagente ou Maestri, encaminha a coordenacao ao team-orchestrator.
---

# Workflow Orchestrator

## Objetivo
Preservar o nome historico enquanto separa planejamento e execucao. Fluxos
single-agent continuam usando `workflow-planner` e `workflow-runner`; pedidos
explicitos de equipe multiagente, lanes ou Maestri usam `team-orchestrator`.

## Quando usar
- Quando um consumidor existente ainda invoca `workflow-orchestrator`.
- Quando o pedido explicita Maestri, equipe multiagente, developer/tester/reviewer
  separados ou um agente coordenando outros agentes.
- Antes de features grandes, auditorias, refatoracoes ou releases ainda nao
  inicializadas no kernel.
- Para migrar uma orquestracao antiga sem quebrar o nome publico.

## Quando nao usar
- Para implementar codigo diretamente.
- Para misturar criacao do plano e execucao de tarefas no mesmo papel.
- Quando `framework-next` ja retornou um asset especifico.

## Entradas esperadas
- Objetivo, contexto e restricoes conhecidos.
- Estado persistente, quando existir.
- Intencao: planejar ou retomar execucao.

## Workflow
1. Emita aviso curto: este nome preserva compatibilidade.
2. Detecte primeiro se a intencao e multiagente.
3. Se houver Maestri/equipe/lanes/workers, encaminhe para `team-orchestrator`
   e `workflows/multi-agent-development.md`.
4. Caso contrario, use `agent-framework-router`; tarefas `fast` nao entram
   neste alias.
5. Rode `framework-next` somente para retomada persistente ou modo `critical`.
6. Em `standard`, encaminhe plano curto a `workflow-planner`/`workflow-runner`.
7. Em `critical`, preserve os papeis separados e a maquina de estados.
8. Preserve entradas antigas como contexto opcional; estado persistente prevalece
   quando pertence a tarefa ativa.
9. Nunca permita que o alias implemente uma tarefa ou ignore transicao `critical`.

## Saida obrigatoria
- Aviso de compatibilidade.
- Estado detectado, quando houver.
- Asset de destino: `team-orchestrator`, `workflow-planner` ou `workflow-runner`.
- Proxima operacao unica.

## Criterios de aceite
- Chamadas antigas continuam resolvendo.
- Planejamento e execucao permanecem separados no fluxo single-agent.
- Multiagente preserva um unico control plane e workers com escopo fechado.
- Estado e transicoes do kernel nao podem ser contornados.
- O destino recebe entradas antigas sem trata-las como evidencia.

## Arquivos de apoio
- Planner: ../../skills/workflow-planner/SKILL.md
- Runner: ../../skills/workflow-runner/SKILL.md
- Retomada: ../../skills/framework-next/SKILL.md
- Time multiagente: ../../skills/team-orchestrator/SKILL.md
- Workflow multiagente: ../../workflows/multi-agent-development.md
- Migracao: ../../docs/kernel-migration.md

## Exemplos de uso
- Codex: `$workflow-orchestrator Planeje esta feature.` → `workflow-planner`
- Claude Code: `/workflow-orchestrator Retome este plano.` → `workflow-runner`
