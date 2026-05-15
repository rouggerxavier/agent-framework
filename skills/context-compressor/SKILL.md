---
name: context-compressor
description: Use para comprimir conversa longa ou estado de trabalho em resumo operacional com decisoes, arquivos, pendencias, riscos e prompt de retomada.
---

# Context Compressor

## Objetivo
Preservar o estado essencial de uma conversa longa para outro agente, modelo, chat ou humano continuar sem reler tudo.

## Quando usar
- Antes de trocar de agente, modelo ou conversa.
- Quando a thread ficou longa.
- Antes de handoff ou retomada futura.

## Quando nao usar
- Para documentacao permanente detalhada.
- Quando o estado atual cabe em poucas frases.
- Para esconder falhas, bloqueios ou incertezas.

## Entradas esperadas
- Conversa, notas, diff, logs ou resumo parcial.
- Destino: Codex, Claude Code, ChatGPT ou humano.
- Nivel de detalhe desejado.

## Workflow
Siga `../../workflows/long-conversation-handoff.md`. Especifico desta skill:
1. Extraia objetivo original e estado atual.
2. Separe decisoes, arquivos, pendencias, riscos e lacunas.
3. Termine com proximos passos e prompt de retomada.

## Saida obrigatoria
Preencha `../../templates/handoff-summary.md` (estado, decisoes, arquivos,
pendencias, riscos, proximos passos, prompt de retomada).

## Criterios de aceite
- O resumo deve permitir continuidade sem reler a conversa.
- Nao omitir bloqueadores, falhas de teste ou incertezas.
- Caminhos e comandos exatos; curto e priorizado.

## Arquivos de apoio
Nao copie estes checklists na skill; aplique-os a partir daqui.
- Workflow: ../../workflows/long-conversation-handoff.md
- Template: ../../templates/handoff-summary.md

## Exemplos de uso
- Codex: `$context-compressor Comprima esta conversa para continuar em outro agente.`
- Claude Code: `/context-compressor Gere handoff curto com prompt de retomada.`
