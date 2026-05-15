---
name: handoff-builder
description: Use para criar handoff claro entre agentes ou humanos com contexto, decisoes, arquivos alterados, comandos, estado atual e proximos passos.
---

# Handoff Builder

## Objetivo
Produzir handoff compacto e suficiente para outra pessoa ou agente continuar sem redescobrir contexto.

## Quando usar
- Ao trocar de agente, modelo, pessoa ou sessao.
- Antes de pausar uma tarefa incompleta.
- Depois de implementacao, auditoria ou QA.

## Quando nao usar
- Para comprimir conversa enorme; use `context-compressor` primeiro.
- Para documentacao permanente longa.
- Para esconder falhas de teste ou pendencias.

## Entradas esperadas
- Trabalho realizado ou estado atual.
- Arquivos, comandos, testes e decisoes.
- Pendencias, riscos ou perguntas abertas.
- Destinatario do handoff.

## Workflow
1. Resuma objetivo original e estado atual.
2. Liste decisoes tomadas e motivo.
3. Registre arquivos ou artefatos alterados.
4. Inclua comandos executados e resultados relevantes.
5. Descreva pendencias, riscos e proximo passo.

## Saida obrigatoria
- Contexto breve.
- Estado atual.
- Mudancas feitas.
- Validacao executada.
- Pendencias e riscos.
- Proximo passo recomendado.

## Criterios de aceite
- O handoff deve ser curto e operacional.
- Nao omitir falhas ou lacunas.
- Use caminhos e comandos exatos quando existirem.
- Separe fatos de recomendacoes.

## Exemplos de uso
- Codex: `$handoff-builder Crie um handoff para outro agente continuar esta feature.`
- Claude Code: `/handoff-builder Resuma o estado atual antes de trocar de agente.`
