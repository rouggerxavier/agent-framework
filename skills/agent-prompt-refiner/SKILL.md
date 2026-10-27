---
name: agent-prompt-refiner
description: Use para escrever ou corrigir system prompt e descricoes de tool de agentes - prompt curto, sem regra de forma - e para corrigir comportamento medido pelo menor ajuste.
---

# Agent Prompt Refiner

## Objetivo
Manter o prompt curto e as descricoes de tool precisas, porque sao as alavancas mais
baratas de comportamento. Corrigir falha medida com o menor texto possivel. Regra
completa em `../../rubrics/agent-design.md`.

## Quando usar
- Ao escrever o system prompt e as descricoes de tool de um agente.
- Quando uma conversa mostrou falha de comportamento (encaminha demais, promete sem
  chamar tool, inventa fato).
- Ao trocar de modelo e ajustar o texto ao tier novo.

## Quando nao usar
- Pedido simples sem tools nem comportamento recorrente: use `prompt-refiner`.
- Falha que o texto nao resolve depois de duas tentativas medidas: suba na escada
  (dado pronto, contrato tipado) com `agent-builder`.
- Escolha de modelo: use `model-routing`.

## Entradas esperadas
- Prompt e descricoes de tool atuais.
- Falha observada: conversa, turno, tool chamada ou nao chamada, frequencia.
- Modelo e tier.

## Workflow
1. Ache o lugar da falha: a decisao depende de uma tool? Corrija primeiro a
   descricao da tool (o que cada opcao cobre e nao cobre).
2. So depois o prompt: 1 a 4 frases de intencao, nunca frase obrigatoria, ordem fixa
   ou palavra proibida.
3. Remova o que conflita com KB ou dados (ex.: texto da KB lido como ordem).
4. Se o modelo erra conta ou comparacao, nao explique no prompt: peca o dado pronto
   no resultado da tool.
5. Ajuste pelo tier: modelo medio/pequeno pede descricoes mais explicitas, nao
   prompt mais longo.
6. Meca so os cenarios afetados mais controle (`agent-eval-planner`).

## Saida obrigatoria
- Diff do prompt/descricoes, com contagem de palavras antes e depois.
- Falha que motivou cada frase e cenario que a mede.
- Resultado da medicao ou a medicao pendente declarada.

## Criterios de aceite
- Prompt cobre identidade, objetivo, tom, origem dos fatos, limites, encaminhamento,
  emergencia e honestidade sobre ser IA, sem regra de forma.
- Cada frase nova aponta a falha que corrige.
- Prompt nao cresce por acumulo: frase que nao mostrou ganho sai.
- Modelo/provider nao aparecem no texto do prompt.

## Arquivos de apoio
- Rubric: ../../rubrics/agent-design.md
- Template: ../../templates/action-prompt-package.md
- Medicao: ../../skills/agent-eval-planner/SKILL.md
- Tools: ../../skills/agent-tool-designer/SKILL.md

## Exemplos de uso
- Codex: `$agent-prompt-refiner O agente encaminha para a equipe toda pergunta sem fonte.`
- Claude Code: `/agent-prompt-refiner Ajuste prompt e tools para o modelo novo, mais barato.`
