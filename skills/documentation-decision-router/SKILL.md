---
name: documentation-decision-router
description: Use para decidir quando criar ADR, README update, runbook, changelog, prompt/package docs, release notes ou nenhuma documentacao.
---

# Documentation Decision Router

## Objetivo
Decidir se uma mudanca precisa de documentacao e qual formato usar, evitando tanto falta de contexto quanto docs desnecessarias.

## Quando usar
- Depois de mudanca em arquitetura, agente, modelo/provider, tool permission, guardrail, API, env, deploy, dados ou runtime.
- Antes de PR, release ou handoff quando alguem precisara operar, revisar ou manter a mudanca.
- Quando ha duvida entre ADR, README, runbook, changelog, prompt docs, release notes ou nada.
- Quando o custo de redescobrir a decisao pode ser maior que manter a doc.

## Quando nao usar
- Para escrever a doc final de agente; use `agent-doc-writer`.
- Para auditar se docs existentes estao sincronizadas; use `docs-sync-auditor`.
- Para mudanca trivial sem impacto de uso, operacao, contrato ou decisao.

## Entradas esperadas
- Objetivo, diff/resumo e areas afetadas.
- Decisoes tomadas, tradeoffs, riscos e reversibilidade.
- Publico: dev, operador, usuario, reviewer, cliente API ou suporte.
- Docs existentes e gaps conhecidos.

## Workflow
1. Identifique o que mudou: comportamento, contrato, config, operacao, arquitetura, agente, tool, guardrail ou release.
2. Avalie custo de redescoberta, reversibilidade, risco operacional e publico afetado.
3. Escolha formato:
   - `none`: trivial ou ja coberto;
   - `README update`: uso/setup/comando mudou;
   - `ADR`: decisao dificil de reverter ou tradeoff relevante;
   - `runbook`: operacao, incidentes, logs, rollback ou troubleshooting;
   - `agent docs`: agente, tools, config, guardrails, evals ou prompt package;
   - `changelog/release notes`: comunicacao de mudanca externa ou breaking change.
4. Prefira atualizar doc existente a criar nova.
5. Liste conteudo minimo e dono da atualizacao.
6. Se ADR ou agente for necessario, encaminhe para `architecture-decision` ou `agent-doc-writer`.

## Saida obrigatoria
Preencha `../../templates/documentation-decision.md` com decisao, formato, justificativa, conteudo minimo e riscos se adiar.

## Criterios de aceite
- Nao criar doc nova quando uma atualizacao curta resolve.
- ADR so quando ha tradeoff real, reversibilidade baixa ou impacto duradouro.
- Runbook so quando alguem precisara operar, debugar ou fazer rollback.
- Decisao `none` deve explicar por que nao aumenta risco.

## Arquivos de apoio
- Template: ../../templates/documentation-decision.md
- ADR: ../../skills/architecture-decision/SKILL.md
- Docs sync: ../../skills/docs-sync-auditor/SKILL.md
- Agent docs: ../../skills/agent-doc-writer/SKILL.md

## Exemplos de uso
- Codex: `$documentation-decision-router Decida que docs esta mudanca precisa.`
- Claude Code: `/documentation-decision-router Escolha ADR, README, runbook, changelog ou nada.`
