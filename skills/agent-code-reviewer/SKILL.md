---
name: agent-code-reviewer
description: Use para revisar diffs de agentes com foco em prompts, tools, guardrails, config, model routing, observabilidade, fallback, seguranca e testes.
---

# Agent Code Reviewer

## Objetivo
Revisar mudancas em agentes com foco em bugs reais, regressao de comportamento, unsafe tool use, prompt fragil, config insegura, logs ruins e validacao insuficiente.

## Quando usar
- Quando o diff toca agente, prompt/system instructions, tools, memoria, model/provider policy, fallback, guardrails ou evals.
- Ao revisar mudanca em runtime agentico, tool registry, logs, tracing, env vars ou config de provider.
- Depois de `code-review-gate` classificar review como `deep` para agente.
- Antes de release/handoff de agente usado por outras pessoas.

## Quando nao usar
- Para diff comum sem comportamento agentico; use `diff-reviewer`.
- Para escolher modelo/provider; use `model-flexibility-auditor`.
- Para validar runtime; use `agent-runtime-qa`.

## Entradas esperadas
- Diff, arquivos alterados, objetivo e contrato esperado do agente.
- Agent design, prompt, tool contracts, guardrails, configs e evals quando existirem.
- Testes, runtime QA, logs/evidencias e riscos conhecidos.
- Ambiente/model/provider afetados.

## Workflow
1. Entenda objetivo e comportamento prometido do agente.
2. Revise prompt: escopo, stop conditions, ambiguidades, conflitos, tool instructions e exemplos negativos.
3. Revise tools: schema, permissao, side effects, erro, retry, idempotencia e unsafe requests.
4. Revise config/model: hardcode, provider lock, fallback, env vars, defaults e secrets.
5. Revise guardrails e seguranca: prompt injection, data exfiltration, memoria/state, logs e redaction.
6. Revise observabilidade e QA: evals, runtime QA, logs, correlation id, custo, regressao e cobertura do objetivo.
7. Reporte achados por severidade antes do resumo, com evidencia e correcao minima.

## Saida obrigatoria
Preencha `../../templates/agent-code-review-report.md` com achados, evidencias, testes faltantes, risco residual e decisao.

## Criterios de aceite
- Findings antes do resumo, ordenados por severidade.
- Cada achado deve ser bug, regressao, risco de seguranca, contrato quebrado ou teste faltante relevante.
- Nao tratar preferencia de estilo como bloqueador.
- Se runtime QA/evals/logs nao foram executados, marcar lacuna explicitamente.

## Arquivos de apoio
- Template: ../../templates/agent-code-review-report.md
- Review geral: ../../skills/diff-reviewer/SKILL.md
- Tools: ../../skills/tool-contract-auditor/SKILL.md
- Seguranca: ../../skills/agent-security-auditor/SKILL.md
- Runtime: ../../skills/agent-runtime-qa/SKILL.md

## Exemplos de uso
- Codex: `$agent-code-reviewer Revise este diff de agente antes do PR.`
- Claude Code: `/agent-code-reviewer Audite prompt, tools, guardrails e fallback desta mudanca.`
