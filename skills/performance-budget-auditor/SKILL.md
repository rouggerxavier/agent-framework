---
name: performance-budget-auditor
description: Use para auditar budget de performance em backend e agentes: latencia, custo, memoria, queries, batch, cache, timeout e medicao.
---

# Performance Budget Auditor

## Objetivo
Avaliar impacto de performance e custo com budget proporcional, recomendando medicao, mitigacao e gates antes de release.

## Quando usar
- Antes de release ou PR que altera caminho critico, API, jobs, queries, cache, batch, agent runtime ou integracao externa.
- Quando ha risco de latencia, custo, memoria, CPU, timeout, N+1, fan-out, retry ou overload.
- Ao revisar mudanca que adiciona chamadas de modelo, tool calls, tarefas em background ou dados volumosos.
- Quando nao existe baseline e a performance importa.

## Quando nao usar
- Para micro-otimizacao sem risco perceptivel ou operacional.
- Para otimizar agente em detalhe; use `agent-optimization-auditor`.
- Para QA funcional pura; use `runtime-qa-audit`.

## Entradas esperadas
- Mudanca, diff ou fluxo a auditar.
- Baseline/budget conhecido, se existir.
- Volumes esperados, SLA, timeout, custo permitido e ambiente.
- Comandos, traces, logs, queries, metrics ou estimativas disponiveis.

## Workflow
1. Identifique caminho critico e budget: latencia, custo, memoria, CPU, timeout, throughput ou tokens.
2. Compare baseline observado, estimado ou ausente.
3. Audite riscos: queries, indices, N+1, cache, batching, pagination, retries, fan-out, model calls, tool calls e jobs.
4. Classifique risco: `low`, `medium`, `high`, `blocked`.
5. Recomende mitigacao minima e medicao: benchmark, trace, load test leve, query plan, runtime QA ou monitoramento.
6. Declare decisao: aceitar, aceitar com guardrails, medir antes, bloquear ou adiar otimizacao.

## Saida obrigatoria
Preencha `../../templates/performance-budget-report.md` com budget, baseline, riscos, mitigacoes, medicao e decisao.

## Criterios de aceite
- Separar medicao real de estimativa.
- Nao exigir benchmark pesado para mudanca de baixo risco.
- Mudanca em caminho critico sem baseline deve ter medicao recomendada ou risco aceito.
- Custo de modelo/tool call entra como performance operacional.

## Arquivos de apoio
- Template: ../../templates/performance-budget-report.md
- Rubric: ../../rubrics/performance-budget.md
- Testes: ../../skills/test-confidence-mapper/SKILL.md
- Runtime QA: ../../skills/runtime-qa-audit/SKILL.md

## Exemplos de uso
- Codex: `$performance-budget-auditor Audite latencia, queries e custo desta feature.`
- Claude Code: `/performance-budget-auditor Revise budget de performance antes do release.`
