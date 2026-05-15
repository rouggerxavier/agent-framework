---
name: prompt-refiner
description: Use para transformar pedidos brutos em prompts claros, testaveis e especificos para Codex, Claude Code, ChatGPT ou agentes.
---

# Prompt Refiner

## Objetivo
Converter uma intencao ambigua em prompt operacional com contexto, escopo, restricoes, saida esperada e criterios de aceite.

## Quando usar
- Antes de delegar tarefa para agente ou modelo.
- Quando o pedido tem ambiguidade, escopo amplo ou formato de saida indefinido.
- Quando e preciso adaptar o mesmo pedido para Codex, Claude Code ou ChatGPT.

## Quando nao usar
- Para tarefas triviais que ja estao claras.
- Para substituir leitura de codigo ou validacao real.
- Para esconder incertezas; marque-as explicitamente.

## Entradas esperadas
- Prompt original ou ideia solta.
- Ferramenta alvo.
- Resultado desejado, restricoes e contexto minimo.

## Workflow
1. Extraia objetivo, contexto, escopo e restricoes.
2. Separe requisitos obrigatorios de preferencias.
3. Remova conflitos e ambiguidades.
4. Adicione formato de saida e criterios de aceite.
5. Gere versao pronta para uso.

## Saida obrigatoria
- Prompt refinado.
- Suposicoes.
- Criterios de aceite.
- Perguntas bloqueantes, se existirem.

## Criterios de aceite
- O prompt deve ser executavel sem explicacao adicional.
- Deve limitar escopo e preservar contexto essencial.
- Deve incluir verificacao quando houver codigo, UI, API ou release.
- Nao deve inventar contexto ausente.

## Exemplos de uso
- Codex: `$prompt-refiner Melhore este pedido para uma tarefa de bugfix.`
- Claude Code: `/prompt-refiner Transforme esta ideia em prompt para refatoracao segura.`
