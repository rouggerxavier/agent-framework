---
name: agent-eval-planner
description: Use para planejar evals simples de agentes com casos, expected behavior, allowed variance, failure modes, regressao e criterios de aceite.
---

# Agent Eval Planner

## Objetivo
Criar um conjunto pequeno e verificavel de evals para agentes, cobrindo comportamento esperado, variancia permitida, falhas e regressao.

## Quando usar
- Antes de mudar prompt, modelo, provider, tools, guardrails ou memoria de agente.
- Quando runtime QA mostrou cenarios que devem virar regressao.
- Para agentes recorrentes que precisam manter padrao sem suite pesada.
- Ao preparar release ou migracao de modelo/provider.

## Quando nao usar
- Para testar tool isolada; use `tool-runtime-validator`.
- Para QA manual rodando; use `agent-runtime-qa`.
- Para inventar metricas abstratas sem casos representativos.

## Entradas esperadas
- Objetivo do agente, contrato de saida e tasks principais.
- Exemplos reais ou sinteticos permitidos.
- Falhas conhecidas, riscos, guardrails e variancia aceitavel.
- Como executar evals ou validar outputs, se ja existir.

## Workflow
1. Escolha 5-12 casos proporcionais ao risco: happy path, edge, bad input, unsafe request, tool failure e fallback.
2. Para cada caso, defina input, contexto minimo, expected behavior, allowed variance e forbidden behavior.
3. Defina avaliacao: exata, schema, rubric curta, humano, snapshot ou runtime assertion.
4. Marque casos que bloqueiam release e casos apenas informativos.
5. Inclua regressao para bugs ja corrigidos e guardrails criticos.
6. Recomende comando/harness minimo e quando atualizar os evals.

## Saida obrigatoria
Preencha `../../templates/agent-eval-plan.md` com casos, criterio, execucao, bloqueadores e manutencao.

## Criterios de aceite
- Cada eval tem comportamento esperado e variancia permitida.
- Casos unsafe ou fora de escopo incluem o que o agente deve recusar, perguntar ou parar.
- Nao depender de julgamento subjetivo quando schema/assertion simples resolve.
- Incluir regressao para bug ou risco critico conhecido.

## Arquivos de apoio
- Template: ../../templates/agent-eval-plan.md
- Testes: ../../skills/test-strategy-builder/SKILL.md
- Confianca: ../../skills/test-confidence-mapper/SKILL.md
- Runtime QA: ../../skills/agent-runtime-qa/SKILL.md

## Exemplos de uso
- Codex: `$agent-eval-planner Monte evals simples para migrar este agente de modelo.`
- Claude Code: `/agent-eval-planner Crie casos de regressao para prompt, tools e guardrails.`
