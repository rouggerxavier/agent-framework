---
name: agent-doc-writer
description: Use para documentar agentes com objetivo, tools, config, env, guardrails, evals, runtime QA, observabilidade, runbook e troubleshooting.
---

# Agent Doc Writer

## Objetivo
Criar ou atualizar documentacao operacional de agente para que outra pessoa consiga configurar, operar, validar e debugar sem redescobrir o design.

## Quando usar
- Depois de criar ou refatorar agente usado por outras pessoas ou fluxo recorrente.
- Quando agente tem tools, env vars, provider/model policy, memoria, guardrails, evals, logs ou runtime QA.
- Antes de PR, release, handoff ou instalacao em outro ambiente.
- Quando `documentation-decision-router` escolhe `agent docs`.

## Quando nao usar
- Para decisao arquitetural isolada; use `architecture-decision`.
- Para sincronizar docs existentes sem escrever nova doc; use `docs-sync-auditor`.
- Para agente experimental sem uso recorrente nem risco operacional.

## Entradas esperadas
- Agent design, prompt/package, tool contracts, configs/env e guardrails.
- Evals, runtime QA, logs/observabilidade e known issues.
- Publico da doc: dev, operador, usuario interno ou reviewer.
- Local desejado da doc, se existir.

## Workflow
1. Identifique publico e objetivo da doc.
2. Resuma agente: objetivo, quando usar, entradas, saidas e fora de escopo.
3. Documente tools, permissoes, side effects, erros e limites.
4. Documente config/env, model/provider policy, fallback, memoria/state e dados que nao devem ser armazenados.
5. Documente guardrails, evals, runtime QA, logs, correlation id, custos e troubleshooting.
6. Inclua runbook minimo: setup, executar, validar, falhas comuns, rollback/desativacao e quando escalar.
7. Evite secrets, prompts sensiveis ou exemplos que exponham dados privados.

## Saida obrigatoria
Preencha `../../templates/agent-doc.md` ou atualize doc existente com as secoes minimas aplicaveis.

## Criterios de aceite
- Doc permite configurar e validar o agente sem conversar com o autor.
- Tools, env vars, guardrails e failure modes ficam claros.
- Evals/runtime QA e troubleshooting aparecem quando existem.
- Nao incluir secrets, tokens, dados sensiveis ou prompt interno que nao deve ser publico.

## Arquivos de apoio
- Template: ../../templates/agent-doc.md
- Agent design: ../../templates/agent-design.md
- Docs decision: ../../skills/documentation-decision-router/SKILL.md
- Docs sync: ../../skills/docs-sync-auditor/SKILL.md

## Exemplos de uso
- Codex: `$agent-doc-writer Documente este agente para operacao e handoff.`
- Claude Code: `/agent-doc-writer Crie doc com tools, env, guardrails, evals e troubleshooting.`
