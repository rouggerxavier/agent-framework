---
name: workflow-orchestrator
description: Use como alias compativel para rotear metas complexas ao workflow-planner e, quando solicitado, ao workflow-runner sob o protocolo persistente.
---

# Workflow Orchestrator

## Objetivo
Preservar o nome historico enquanto separa planejamento e execucao. Novos fluxos
devem invocar `workflow-planner` e `workflow-runner` diretamente.

## Quando usar
- Quando um consumidor existente ainda invoca `workflow-orchestrator`.
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
1. Emita aviso curto: este nome e um alias de compatibilidade.
2. Use `agent-framework-router`; tarefas `fast` nao entram neste alias.
3. Rode `framework-next` somente para retomada persistente ou modo `critical`.
4. Em `standard`, encaminhe plano curto a `workflow-planner`/`workflow-runner`.
5. Em `critical`, preserve os papeis separados e a maquina de estados.
6. Preserve entradas antigas como contexto opcional; estado persistente prevalece
   quando pertence a tarefa ativa.
7. Nunca permita que o alias implemente uma tarefa ou ignore transicao `critical`.

## Saida obrigatoria
- Aviso de compatibilidade.
- Estado detectado, quando houver.
- Asset de destino: `workflow-planner` ou `workflow-runner`.
- Proxima operacao unica.

## Criterios de aceite
- Chamadas antigas continuam resolvendo.
- Planejamento e execucao permanecem separados.
- Estado e transicoes do kernel nao podem ser contornados.
- O destino recebe entradas antigas sem trata-las como evidencia.

## Arquivos de apoio
- Planner: ../../skills/workflow-planner/SKILL.md
- Runner: ../../skills/workflow-runner/SKILL.md
- Retomada: ../../skills/framework-next/SKILL.md
- Migracao: ../../docs/kernel-migration.md

## Exemplos de uso
- Codex: `$workflow-orchestrator Planeje esta feature.` → `workflow-planner`
- Claude Code: `/workflow-orchestrator Retome este plano.` → `workflow-runner`
