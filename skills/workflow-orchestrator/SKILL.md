---
name: workflow-orchestrator
description: Use para decompor metas complexas em fases, escolher skills, modelo, effort, necessidade de subagents, riscos e plano de execucao.
---

# Workflow Orchestrator

## Objetivo
Transformar uma meta ampla em um plano operacional com fases, skills, modelo recomendado, effort recomendado, uso ou nao de subagents, riscos e criterios de passagem.

## Quando usar
- Antes de features grandes, auditorias, refatoracoes ou releases.
- Quando varias skills podem ser combinadas.
- Quando e preciso dividir trabalho entre Codex, Claude Code, ChatGPT, subagents ou humano.

## Quando nao usar
- Para tarefa pequena com proximo passo obvio.
- Para executar codigo diretamente sem planejamento.
- Quando o usuario pediu apenas uma resposta pontual.

## Entradas esperadas
- Objetivo final e contexto do projeto.
- Prazo, restricoes, risco e ferramentas disponiveis.
- Estado atual, artefatos existentes e criterios de sucesso.

## Workflow
1. Defina resultado final, escopo e criterios de sucesso.
2. Escolha skills relevantes para cada fase.
3. Recomende modelo/agente e effort por fase: low, medium, high ou xhigh.
4. Decida se subagents ajudam; use apenas para subtarefas independentes e bem delimitadas.
5. Liste riscos, dependencias, checkpoints e plano por fases.
6. Indique a primeira acao concreta.

## Saida obrigatoria
- Plano por fases.
- Skills a usar em cada fase.
- Modelo/agente e effort recomendados.
- Decisao sobre subagents e motivo.
- Riscos, dependencias e checkpoints.
- Primeiro passo recomendado.

## Criterios de aceite
- Cada fase deve ter entrada, saida e criterio de conclusao.
- O plano deve evitar trabalho duplicado entre agentes.
- Subagents so devem ser recomendados quando houver tarefas paralelas independentes.
- O primeiro passo precisa ser executavel imediatamente.

## Exemplos de uso
- Codex: `$workflow-orchestrator Planeje a entrega desta feature com fases, skills e riscos.`
- Claude Code: `/workflow-orchestrator Organize esta refatoracao entre agentes e checks.`
