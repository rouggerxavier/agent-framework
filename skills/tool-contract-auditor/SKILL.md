---
name: tool-contract-auditor
description: Use para auditar contratos de tools de agente: schema, payloads, erros, permissao, side effects, timeout, retry, idempotencia e logs.
---

# Tool Contract Auditor

## Objetivo
Detectar riscos de quebra, ambiguidade, permissao excessiva ou comportamento imprevisivel em tools usadas por agentes.

## Quando usar
- Ao revisar tool implementada ou diff que altera schema, permissao, erro ou side effect.
- Antes de liberar agent tool para uso recorrente ou multiusuario.
- Quando tool chama API, banco, filesystem, rede, subprocesso ou provider externo.
- Quando o agente falha por argumentos ambiguos, erro nao tratado ou retry perigoso.

## Quando nao usar
- Para desenhar tool do zero; use `agent-tool-designer`.
- Para testar comportamento rodando; use `tool-runtime-validator`.
- Para contrato HTTP publico puro; use `api-contract-auditor`.

## Entradas esperadas
- Codigo, schema, docs ou manifest da tool.
- Exemplos de chamadas, payloads e erros.
- Permissoes, side effects, usuarios/consumidores e runtime.
- Mudanca pretendida ou diff, se houver.

## Workflow
1. Identifique contrato publico da tool: nome, descricao, input schema, output schema, erros e side effects.
2. Audite schema: obrigatorios, tipos, enums, limites, defaults, nullable, compatibilidade e exemplos.
3. Audite comportamento: auth, permissao, timeout, retry, idempotencia, partial success e rollback.
4. Audite seguranca: secrets, logs, dados sensiveis, prompt injection via tool output e permissao excessiva.
5. Classifique achados como `blocker`, `high`, `medium` ou `low`.
6. Recomende mitigacao, teste de contrato e atualizacao de docs/prompt quando necessario.

## Saida obrigatoria
Preencha `../../templates/tool-contract-report.md` com achados, evidencia, compatibilidade, riscos e verificacao.

## Criterios de aceite
- Diferenciar contrato da tool de detalhe interno.
- Nao aprovar permissao ampla sem justificativa e guardrail.
- Toda alteracao breaking precisa de migracao, fallback ou comunicacao.
- Incluir teste/QA para schema, erro, timeout e side effect relevante.

## Arquivos de apoio
- Template: ../../templates/tool-contract-report.md
- API: ../../skills/api-contract-auditor/SKILL.md
- Seguranca: ../../skills/security-privacy-audit/SKILL.md
- Review: ../../skills/diff-reviewer/SKILL.md

## Exemplos de uso
- Codex: `$tool-contract-auditor Audite schema e permissoes desta tool antes do merge.`
- Claude Code: `/tool-contract-auditor Revise contrato, erros e idempotencia deste diff.`
