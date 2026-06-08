---
name: agent-optimization-auditor
description: Use para otimizar agentes quanto a tokens, latencia, tool calls, retries, cache, prompt size, model tier, contexto carregado e custo.
---

# Agent Optimization Auditor

## Objetivo
Reduzir custo, latencia e complexidade de agentes sem degradar qualidade, seguranca, guardrails ou capacidade de debug.

## Quando usar
- Depois que o agente funciona e tem runtime QA/evals minimos.
- Quando ha custo alto, latencia alta, contexto grande, muitas tool calls, retries excessivos ou prompt inchado.
- Antes de migrar model tier, cache, batching, prompt compression ou routing.
- Quando o agente carrega contexto demais ou usa modelo forte para tarefas simples.

## Quando nao usar
- Antes de validar comportamento basico do agente.
- Para escolher modelo sem medir tarefa/risco; use `model-routing` ou `model-flexibility-auditor`.
- Para performance geral backend; use `performance-budget-auditor`.

## Entradas esperadas
- Objetivo do agente, prompt, tools, evals e runtime QA.
- Logs/traces/custos/latencia, se existirem.
- Model/provider policy, contexto carregado, cache/retry/fallback e limites.
- Riscos de qualidade, seguranca e privacidade.

## Workflow
1. Estabeleca baseline: latencia, custo/tokens, tool calls, retries, contexto e qualidade observada.
2. Procure desperdicio: prompt longo, contexto irrelevante, tool call redundante, retry ruidoso, modelo caro demais, cache ausente ou fallback mal usado.
3. Classifique otimizacoes:
   - `safe`: remove ruido sem mudar comportamento;
   - `needs eval`: pode mudar qualidade;
   - `risky`: afeta guardrails, seguranca, contrato ou output.
4. Recomende mudancas: prompt compression, context gating, tool batching, cache, timeout, model tier routing ou eval regression.
5. Exija verificacao: evals, runtime QA, custo/latencia antes/depois e review quando aplicavel.

## Saida obrigatoria
Preencha `../../templates/agent-optimization-report.md` com baseline, achados, recomendacoes, risco e verificacao.

## Criterios de aceite
- Nao otimizar removendo guardrail, validacao ou logs essenciais.
- Toda troca de modelo/tier precisa criterio de qualidade e fallback.
- Diferenciar economia real de micro-otimizacao.
- Recomendacao de alto risco precisa eval/runtime QA antes de aceitar.

## Arquivos de apoio
- Template: ../../templates/agent-optimization-report.md
- Model routing: ../../skills/model-routing/SKILL.md
- Observability: ../../skills/agent-observability-auditor/SKILL.md
- Runtime QA: ../../skills/agent-runtime-qa/SKILL.md

## Exemplos de uso
- Codex: `$agent-optimization-auditor Reduza custo e latencia deste agente sem perder qualidade.`
- Claude Code: `/agent-optimization-auditor Audite prompt size, tool calls, cache e model tier.`
