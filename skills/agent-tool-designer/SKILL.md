---
name: agent-tool-designer
description: Use para desenhar tools de agentes com nome, schema, permissao, side effects, erros, timeout, retry, idempotencia e exemplos.
---

# Agent Tool Designer

## Objetivo
Projetar tools de agente antes da implementacao, com contrato claro, permissao minima, erro previsivel e validacao possivel.

## Quando usar
- Ao criar tool nova para agente, subagente, skill, MCP, API wrapper ou automacao.
- Quando uma tool toca arquivos, rede, banco, secrets, pagamentos, usuarios ou sistemas externos.
- Antes de implementar tool com side effects, permissao ampla ou schema incerto.
- Ao refatorar tool mal nomeada, acoplada ou dificil de testar.

## Quando nao usar
- Para chamada interna simples sem fronteira de agente.
- Para auditar tool ja pronta; use `tool-contract-auditor`.
- Para validar em execucao; use `tool-runtime-validator`.

## Entradas esperadas
- Objetivo da tool e tarefa do agente que ela habilita.
- Inputs, outputs, erros esperados e consumidores.
- Side effects, permissoes, dados sensiveis e limites operacionais.
- Ambiente de runtime, timeout, retry e observabilidade desejada.

## Workflow
1. Defina nome com verbo claro, escopo estreito e sem provider hardcoded se houver alternativa.
2. Especifique schema: campos obrigatorios, tipos, enums, limites, defaults e exemplos.
3. Defina permissao e side effects: leitura/escrita, rede, arquivos, dados, rate limit e confirmacao humana.
4. Modele erros: validacao, auth, not found, timeout, provider failure, partial success e unsafe request.
5. Decida idempotencia, retry, timeout, cache e rollback quando houver escrita.
6. Defina observabilidade minima: logs seguros, correlation id, custo, latencia e auditoria.

## Saida obrigatoria
Preencha `../../templates/agent-tool-design.md` com contrato, permissoes, erros, exemplos e validacao.

## Criterios de aceite
- Tool tem responsabilidade unica e nome que descreve acao real.
- Schema e restritivo o bastante para impedir input ambiguo.
- Side effects e permissoes estao explicitos antes da implementacao.
- Erros e timeout tem contrato previsivel para o agente.
- Ha pelo menos um exemplo feliz, um invalido e um de falha externa.

## Arquivos de apoio
- Template: ../../templates/agent-tool-design.md
- Agente: ../../skills/agent-builder/SKILL.md
- Prompt: ../../skills/agent-prompt-refiner/SKILL.md
- Seguranca: ../../skills/security-privacy-audit/SKILL.md

## Exemplos de uso
- Codex: `$agent-tool-designer Desenhe uma tool para buscar pedidos com permissao minima.`
- Claude Code: `/agent-tool-designer Especifique schema, erros e side effects desta tool.`
