---
name: agent-runtime-qa
description: Use para validar agente em execucao com happy path, bad input, missing env, tool failure, timeout, retry, fallback model e escalation.
---

# Agent Runtime QA

## Objetivo
Validar comportamento real de um agente rodando, cobrindo fluxos felizes, falhas, tools, fallback, custo e escalacao antes de declarar pronto.

## Quando usar
- Depois de implementar ou refatorar agente com prompt, tools, memoria, modelo configuravel ou guardrails.
- Antes de release, merge ou handoff de agente usado por outras pessoas.
- Quando o agente depende de env vars, provider externo, tool runtime, logs ou fallback.
- Para confirmar correcao de bug em comportamento agentico.

## Quando nao usar
- Para revisar apenas codigo; use `diff-reviewer` ou `agent-code-reviewer` quando existir.
- Para validar tool isolada; use `tool-runtime-validator`.
- Quando nao ha ambiente executavel; gere plano de QA e marque bloqueio.

## Entradas esperadas
- Como iniciar o agente, endpoint, CLI, script, notebook ou harness.
- Casos principais, dados de teste seguros e credenciais de teste.
- Contrato esperado: inputs, outputs, tools, guardrails e stop conditions.
- Config de modelo/provider, fallback, timeout e logs.

## Workflow
1. Confirme ambiente, versao, config, modelo/provider e dados de teste.
2. Execute happy path com input minimo e caso representativo.
3. Execute bad input, prompt ambiguo, falta de contexto e pedido fora de escopo.
4. Execute falhas: missing env, tool failure, timeout, retry, provider failure e fallback model.
5. Verifique guardrails: permissao de tool, redacao segura, stop condition, escalacao e logs sem secrets.
6. Registre evidencias, bugs, custo/latencia quando observavel e riscos residuais.

## Saida obrigatoria
Preencha `../../templates/agent-runtime-qa-report.md` com ambiente, cenarios, pass/fail, evidencias, bugs e riscos.

## Criterios de aceite
- Nao declarar aprovado sem listar cenarios executados e ambiente.
- Falhas devem produzir erro util, pergunta, fallback, escalacao ou stop condition.
- Logs/evidencias nao devem expor secrets, tokens ou dados sensiveis.
- Se fallback/model routing nao foi testado, marcar explicitamente.

## Arquivos de apoio
- Template: ../../templates/agent-runtime-qa-report.md
- QA geral: ../../skills/runtime-qa-audit/SKILL.md
- Tools: ../../skills/tool-runtime-validator/SKILL.md
- Evals: ../../skills/agent-eval-planner/SKILL.md

## Exemplos de uso
- Codex: `$agent-runtime-qa Valide este agente rodando com tool failure e fallback.`
- Claude Code: `/agent-runtime-qa Execute QA runtime e registre evidencias.`
