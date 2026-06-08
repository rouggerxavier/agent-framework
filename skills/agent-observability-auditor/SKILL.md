---
name: agent-observability-auditor
description: Use para auditar observabilidade de agentes: logs, traces, metrics, cost tracking, prompt/tool audit, redaction e debug readiness.
---

# Agent Observability Auditor

## Objetivo
Verificar se um agente deixa evidencias suficientes para operar, debugar, medir custo e auditar tool/prompt behavior sem vazar dados sensiveis.

## Quando usar
- Antes de release de agente com tools, provider externo, custo relevante, usuarios externos ou falhas dificeis de reproduzir.
- Quando debug depende de logs, traces, prompt/tool audit, correlation id ou cost tracking.
- Depois de adicionar fallback, retry, cache, memoria, guardrails ou runtime QA.
- Quando incidente ou bug mostrou falta de evidencia.

## Quando nao usar
- Para seguranca geral de agente; use `agent-security-auditor`.
- Para validar comportamento rodando; use `agent-runtime-qa`.
- Para criar dashboards completos sem necessidade atual.

## Entradas esperadas
- Fluxo do agente, tools, provider/model, logs/traces e runtime.
- Dados sensiveis, politica de redaction e ambientes.
- Custo/latencia desejados, IDs de correlacao e exemplos de falha.
- Comandos, screenshots, traces ou logs disponiveis.

## Workflow
1. Mapeie eventos importantes: request, model call, tool call, fallback, retry, guardrail, erro e escalacao.
2. Verifique logs: correlation id, severidade, contexto minimo, redaction e ausencia de secrets.
3. Verifique traces/audit: prompt/tool boundary, tool args seguros, output resumido, decisao e usuario/tenant quando aplicavel.
4. Verifique metricas: latencia, erro, timeout, retry, fallback, custo/tokens e uso de tool.
5. Verifique debug readiness: reproduzir caso, localizar execucao, comparar versao/config e abrir sessao persistente se necessario.
6. Classifique gaps e recomende instrumentacao minima.

## Saida obrigatoria
Preencha `../../templates/agent-observability-report.md` com eventos, gaps, riscos, instrumentacao e verificacao.

## Criterios de aceite
- Observabilidade deve ajudar debug real, nao apenas gerar logs barulhentos.
- Logs e traces nao podem expor secrets, tokens ou dados sensiveis desnecessarios.
- Custo/latencia devem ser medidos ou explicitamente marcados como invisiveis.
- Cada gap recomendado deve ter valor operacional claro.

## Arquivos de apoio
- Template: ../../templates/agent-observability-report.md
- Debug: ../../skills/persistent-debug-session/SKILL.md
- Seguranca: ../../skills/agent-security-auditor/SKILL.md
- Runtime QA: ../../skills/agent-runtime-qa/SKILL.md

## Exemplos de uso
- Codex: `$agent-observability-auditor Audite logs, traces e custo deste agente.`
- Claude Code: `/agent-observability-auditor Verifique debug readiness e redaction antes do release.`
