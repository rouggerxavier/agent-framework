---
name: agent-guardrails-implementer
description: "Use para especificar ou implementar guardrails de agentes: input validation, output constraints, permissions, escalation, stop conditions e audit logs."
---

# Agent Guardrails Implementer

## Objetivo
Definir guardrails praticos para agentes, reduzindo uso inseguro de tools, vazamento de dados, saida fora de contrato e falhas sem escalacao.

## Quando usar
- Ao criar ou refatorar agente com tools, memoria, dados sensiveis, usuarios externos ou side effects.
- Antes de liberar agente recorrente para outras pessoas.
- Quando prompt, runtime ou tool permission precisam de limites claros.
- Depois de auditoria que encontrou risco de prompt injection, permissao ampla, logs ruins ou falta de stop condition.

## Quando nao usar
- Para auditoria sem proposta de guardrail; use `agent-security-auditor`.
- Para seguranca ampla de app sem agente; use `security-privacy-audit`.
- Para tool isolada sem agente; use `agent-tool-designer` ou `tool-contract-auditor`.

## Entradas esperadas
- Objetivo do agente, usuarios, dados processados e outputs esperados.
- Tools, permissoes, side effects, memoria/state e runtime.
- Riscos conhecidos, limites de negocio e requisitos de escalacao.
- Prompt ou design atual, se existir.

## Workflow
1. Mapeie superficies: input, prompt, tools, memoria, output, logs, configs e integracoes.
2. Defina guardrails de entrada: schema, tamanho, tipos, origem, conteudo proibido e ambiguidade.
3. Defina guardrails de tools: allowlist, permissao minima, confirmacao humana, idempotencia, timeout e unsafe requests.
4. Defina guardrails de saida: schema, redacao segura, dados proibidos, citacao de incerteza e output constraints.
5. Defina stop conditions e escalacao: quando perguntar, recusar, parar, pedir humano ou abrir handoff.
6. Defina audit logs seguros: evento, tool, decisao, erro, custo e correlation id sem secrets.

## Saida obrigatoria
Preencha `../../templates/agent-guardrails-plan.md` com guardrails, implementacao, verificacao e riscos residuais.

## Criterios de aceite
- Guardrails cobrem input, tool, output, memoria, logs e escalacao quando aplicavel.
- Permissoes de tool seguem menor privilegio e side effects explicitos.
- Stop conditions sao verificaveis, nao apenas texto generico.
- Logs ajudam debug sem expor secrets, tokens ou dados sensiveis.

## Arquivos de apoio
- Template: ../../templates/agent-guardrails-plan.md
- Agente: ../../skills/agent-builder/SKILL.md
- Tools: ../../skills/tool-contract-auditor/SKILL.md
- Seguranca: ../../skills/agent-security-auditor/SKILL.md

## Exemplos de uso
- Codex: `$agent-guardrails-implementer Especifique guardrails para este agente com tools externas.`
- Claude Code: `/agent-guardrails-implementer Implemente stop conditions e permissoes de tool.`
