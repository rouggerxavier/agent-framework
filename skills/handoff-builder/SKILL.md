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
Siga `../../workflows/agent-handoff.md`. Para conversa longa, rode antes a
skill `context-compressor`. Especifico desta skill:
1. Resuma objetivo, estado atual e decisoes com motivo.
2. Registre arquivos alterados, comandos e resultados.
3. Descreva pendencias, riscos e proximo passo.

## Saida obrigatoria
Preencha `../../templates/handoff-summary.md` (contexto, estado, mudancas,
validacao, pendencias/riscos, proximo passo).

## Criterios de aceite
- Handoff curto e operacional; nao omitir falhas ou lacunas.
- Caminhos e comandos exatos; separe fatos de recomendacoes.

## Arquivos de apoio
Nao copie estes checklists na skill; aplique-os a partir daqui.
- Workflow: ../../workflows/agent-handoff.md
- Template: ../../templates/handoff-summary.md

## Exemplos de uso
- Codex: `$handoff-builder Crie um handoff para outro agente continuar esta feature.`
- Claude Code: `/handoff-builder Resuma o estado atual antes de trocar de agente.`
