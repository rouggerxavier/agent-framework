---
name: framework-next
description: Use para inicializar ou retomar um projeto com estado persistente, validar .agent/STATE.md e escolher uma unica proxima operacao permitida.
---

# Framework Next

## Objetivo

Retomar trabalho sem depender da conversa anterior, usando estado, artefatos,
evidencias e Git observados diretamente.

## Quando usar

- Ao iniciar trabalho em um projeto que pode ou nao possuir `.agent/`.
- Depois de troca de sessao, agente, compactacao, falha ou interrupcao.
- Antes de qualquer transicao quando o estado ou a proxima operacao nao estao claros.

## Quando nao usar

- Para inventar spec, plano, contrato ou evidencia ausente.
- Para implementar a tarefa retornada; encaminhe ao asset indicado.
- Para contornar uma transicao bloqueada.

## Entradas esperadas

- Raiz ou subdiretorio do projeto.
- `.agent/STATE.md` e artefatos referenciados, quando existentes.
- Estado observavel do Git.

## Workflow

1. Rode `scripts/framework-next --project <caminho>` a partir do framework.
2. Se o projeto estiver sem `.agent/`, inicialize somente com autorizacao:
   `scripts/framework-next init --project <caminho> --name <nome> --mode full`.
3. Leia estado, roadmap, contexto, decisoes e artefatos ativos indicados.
4. Trate referencias ausentes, contexto stale, tarefa sem contrato ou Git
   conflitante como inconsistencia; nao fabrique reparos.
5. Siga exatamente a operacao e o asset retornados.
6. Use `transition` somente depois de persistir as evidencias exigidas pela
   maquina de estados.

## Saida obrigatoria

- Current state.
- Detected evidence.
- Inconsistencies.
- Next operation.
- Required asset.
- Blocking conditions.

## Criterios de aceite

- Uma unica proxima operacao.
- Decisao explicada por evidencia observada.
- Estado inconsistente bloqueia execucao.
- Nenhuma transicao proibida ou artefato ausente e inferido.

## Arquivos de apoio

- Protocolo: ../../kernel/protocol.md
- Maquina de estados: ../../kernel/state-machine.md
- Estado: ../../templates/project-state.md
- Runner: ../../skills/workflow-runner/SKILL.md

## Exemplos de uso

- Codex: `$framework-next Retome este projeto pelo estado persistente.`
- Claude Code: `/framework-next Determine a proxima operacao sem usar a conversa anterior.`

