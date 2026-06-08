---
name: agent-builder
description: Use para criar ou refatorar agentes com objetivo, prompt, tools, memoria, modelo configuravel, runtime, guardrails, testes e validacao.
---

# Agent Builder

## Objetivo
Planejar e orientar criacao ou refatoracao de agentes modulares, configuraveis e verificaveis, evitando hardcode, prompt fragil e ausencia de guardrails.

## Quando usar
- Ao criar agente novo, subagente, assistente, workflow agentico ou skill com comportamento operacional.
- Ao refatorar agente existente com prompt, tools, memoria, runtime ou modelo acoplado.
- Quando a tarefa envolve model routing, tool use, guardrails, env vars, runtime validation ou evals.
- Antes de implementar agente que sera usado por outras pessoas ou em fluxo recorrente.

## Quando nao usar
- Para prompt simples sem tools, estado ou runtime.
- Para auditoria sem criacao/refatoracao; use `agent-anti-hardcode-auditor` ou `diff-reviewer`.
- Para agente ja implementado que so precisa QA runtime; use `runtime-qa-audit`.

## Entradas esperadas
- Objetivo do agente e tarefas que ele deve realizar.
- Usuario-alvo, ambiente e restricoes.
- Tools disponiveis ou desejadas, com permissoes e efeitos colaterais.
- Requisitos de modelo/provider, memoria, configs, guardrails e validacao.

## Workflow
Siga `../../workflows/agent-workflow.md`. Especifico desta skill:
1. Refinar o pedido com foco em objetivo, limites, inputs, outputs e falhas esperadas.
2. Preencher `../../templates/agent-design.md`.
3. Definir fronteiras: prompt, tools, memoria/state, configs, runtime e observabilidade.
4. Evitar hardcode de modelo, provider, paths, env vars, tool names e prompt snippets.
5. Definir guardrails: validacao de entrada, permissao de tools, stop conditions, escalacao e logs.
6. Definir validacao: testes, evals simples, runtime QA, code review e criterios de release.

## Saida obrigatoria
- Agent design preenchido ou resumo equivalente.
- Lista de arquivos/modulos provaveis.
- Guardrails e configuracoes obrigatorias.
- Plano de implementacao e validacao.
- Riscos, tradeoffs e perguntas bloqueantes.

## Criterios de aceite
- O agente tem contrato claro de entrada, saida e stop conditions.
- Modelo/provider sao configuraveis ou a decisao de fixar esta justificada.
- Tools tem permissao, erro, timeout, idempotencia e side effects definidos.
- Ha validacao runtime e code review antes de declarar pronto.

## Arquivos de apoio
- Workflow: ../../workflows/agent-workflow.md
- Template: ../../templates/agent-design.md
- Prompt: ../../skills/prompt-refiner/SKILL.md
- Plano backend: ../../skills/backend-slice-planner/SKILL.md
- Testes: ../../skills/test-strategy-builder/SKILL.md

## Exemplos de uso
- Codex: `$agent-builder Planeje um agente para triagem de issues com tools e guardrails.`
- Claude Code: `/agent-builder Refatore este agente para remover hardcode de modelo e validar runtime.`
