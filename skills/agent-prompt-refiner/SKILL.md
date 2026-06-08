---
name: agent-prompt-refiner
description: Use para refinar prompts de agentes, system prompts, tool instructions, guardrails, exemplos negativos, evals e contratos de saida.
---

# Agent Prompt Refiner

## Objetivo
Transformar prompt de agente em contrato operacional claro, modular e testavel, sem acoplar modelo, provider ou tool runtime sem necessidade.

## Quando usar
- Ao criar ou revisar system prompt, developer prompt, skill instructions ou prompt de subagente.
- Quando o agente usa tools, memoria, estado, guardrails, evals ou runtime validation.
- Quando o prompt mistura objetivo, politica, exemplos, tool rules e formato de saida sem fronteiras claras.
- Antes de congelar prompt usado por outros usuarios ou agentes.

## Quando nao usar
- Para pedido simples de uma unica resposta sem tools ou comportamento recorrente.
- Para escolher modelo/provider; use `model-flexibility-auditor`.
- Para implementar o agente inteiro; use `agent-builder`.

## Entradas esperadas
- Prompt atual ou objetivo do agente.
- Tarefas permitidas e tarefas fora de escopo.
- Tools disponiveis, permissoes, erros e side effects.
- Guardrails, dados sensiveis, output esperado e exemplos de falha.

## Workflow
1. Separe o prompt em blocos: missao, escopo, contexto, tools, guardrails, memoria/state, output contract e exemplos.
2. Remova instrucoes duplicadas, conflitantes, vagas ou dependentes de modelo especifico.
3. Defina comportamento para incerteza, falta de contexto, tool failure, dados sensiveis e stop conditions.
4. Escreva tool instructions com schema, permissao, idempotencia, timeout, erro e quando nao chamar.
5. Adicione exemplos negativos curtos para proibicoes fragis, sem ensinar bypass.
6. Defina evals ou runtime QA para validar o prompt em casos reais.

## Saida obrigatoria
Preencha `../../templates/action-prompt-package.md` no modo `agent-build`, incluindo prompt refinado, guardrails, tools permitidas, output contract e verificacao.

## Criterios de aceite
- O prompt deixa claro o que o agente deve fazer, recusar, perguntar e parar.
- Tool use tem regras verificaveis e nao depende de nome hardcoded sem justificativa.
- Modelo/provider ficam configuraveis ou a excecao e documentada.
- Ha pelo menos um caso de validacao feliz, um caso ruim e um caso de tool failure.

## Arquivos de apoio
- Template: ../../templates/action-prompt-package.md
- Agente: ../../skills/agent-builder/SKILL.md
- Anti-hardcode: ../../skills/agent-anti-hardcode-auditor/SKILL.md
- Guardrails: ../../skills/security-privacy-audit/SKILL.md

## Exemplos de uso
- Codex: `$agent-prompt-refiner Refine este system prompt de agente com tools e guardrails.`
- Claude Code: `/agent-prompt-refiner Revise instrucoes de tool e exemplos negativos deste agente.`
