---
name: context-compressor
description: Use para comprimir contexto proporcional ao modo, sem exigir STATE.md fora do lifecycle persistente.
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
1. Confirme o modo.
2. Em `fast`, normalmente nao comprima; se necessario, resuma goal, diff,
   arquivos, testes e riscos sem criar `.agent/`.
3. Em `standard`, resuma plano curto, trabalho concluido, testes, pendencias e
   proximo passo; use `STATE.md` somente se a persistencia tiver sido escolhida.
4. Em `critical`, leia `STATE.md` e artefatos ativos; eles prevalecem sobre a
   conversa.
5. Separe evidencias, comandos, blockers, decisoes, arquivos e riscos.
6. Termine com `framework-next` apenas para retomada persistente
   `standard`/`critical`.

## Saida obrigatoria
- `fast`: resumo inline quando realmente necessario.
- `standard`: resumo leve; template opcional.
- `critical`: preencha `../../templates/handoff-summary.md`.

## Criterios de aceite
- O resumo deve permitir continuidade sem reler a conversa.
- Nao omitir bloqueadores, falhas de teste ou incertezas.
- Caminhos e comandos exatos; curto e priorizado.
- Quando houver `STATE.md`, o handoff o complementa; divergencia e marcada.
- Nao fabricar estado persistente para comprimir tarefa comum.

## Arquivos de apoio
Nao copie estes checklists na skill; aplique-os a partir daqui.
- Workflow: ../../workflows/long-conversation-handoff.md
- Template: ../../templates/handoff-summary.md

## Exemplos de uso
- Codex: `$context-compressor Comprima esta conversa para continuar em outro agente.`
- Claude Code: `/context-compressor Gere handoff curto com prompt de retomada.`
