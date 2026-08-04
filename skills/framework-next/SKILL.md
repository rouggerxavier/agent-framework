---
name: framework-next
description: Use para retomar estado persistente ou inicializa-lo explicitamente; nao e porta de entrada obrigatoria para tarefas comuns.
---

# Framework Next

## Objetivo

Retomar trabalho persistente sem depender da conversa e respeitar o
`execution_mode` registrado.

## Quando usar

- Quando o usuario pedir retomada ou persistencia.
- Quando `.agent/STATE.md` pertencer a tarefa/fase ativa.
- Depois de troca de sessao, agente, compactacao, falha ou interrupcao.
- Antes de qualquer transicao quando o estado ou a proxima operacao nao estao claros.

## Quando nao usar

- Para inventar spec, plano, contrato ou evidencia ausente.
- Para implementar a tarefa retornada; encaminhe ao asset indicado.
- Para contornar uma transicao bloqueada.
- Como porta de entrada obrigatoria de uma tarefa nova `fast`.

## Entradas esperadas

- Raiz ou subdiretorio do projeto.
- `.agent/STATE.md` e artefatos referenciados, quando existentes.
- Estado observavel do Git.

## Workflow

1. Rode `scripts/framework-next --project <caminho>`.
2. Sem `.agent/`, encaminhe para `agent-framework-router`; nao inicialize
   automaticamente.
3. Inicialize somente com pedido/necessidade confirmada. O padrao e `standard`:
   `scripts/framework-next init --project <caminho> --name <nome>` cria somente
   `STATE.md` e `PLAN.md`; acrescente `--persistent` para o kernel completo
   (fases, contratos, gates, ledger) ainda em `standard`. `--mode critical` e
   uma escolha explicita, nunca um padrao.
4. Leia `execution_mode`; estado antigo sem o campo usa `standard`. Silencio nao
   e declaracao de dano grave, e `critical` nunca e inferido.
5. Em `standard`, o ciclo minimo e `start-task` -> implementacao -> testes
   direcionados -> review opcional -> `finish-task`. Gates, seal, ledger e
   reviewers separados continuam disponiveis e nunca sao pre-requisito.
6. Em `critical`, leia todos os artefatos ativos, valide referencias/contexto/Git
   e siga exatamente a operacao retornada.
7. Use transicoes formais somente no lifecycle `critical`, depois da evidencia.
   Fora dele, `start-task` e `finish-task` movem fase e indice juntos.
8. O comando funciona da raiz, de subdiretorio, de CI e de linked worktree; a
   raiz e resolvida por `git rev-parse --show-toplevel`, nunca pelo caminho
   gravado em `STATE.md`.
9. Diante do aviso `git-worktree-legacy`, nao edite `STATE.md` manualmente nem
   trate o projeto como invalido: rode
   `scripts/framework-next normalize-worktree --project <caminho>` uma vez e
   commite o resultado.

## Saida obrigatoria

- Current state.
- Execution mode.
- Detected evidence.
- Inconsistencies.
- Next operation.
- Required asset.
- Blocking conditions.

## Criterios de aceite

- Uma unica proxima operacao.
- Decisao explicada por evidencia observada.
- Fora de `critical`, so bloqueiam: arquivo ilegivel ou ausente, task
  inexistente, blocker aberto para a task, task ja concluida, dependencia
  declarada nao satisfeita e conflito real de branch/worktree. O resto e aviso.
- Nenhuma transicao proibida ou artefato ausente e inferido.
- Ausencia de `.agent/` roteia para `auto`/`fast`, sem criar arquivos.
- Estado antigo sem `execution_mode` continua como `standard`.
- Nenhum caminho absoluto local e gravado em `STATE.md`; `git.worktree` usa `.`.
- Trocar de computador nao produz diff em `STATE.md`.

## Arquivos de apoio

- Protocolo: ../../kernel/protocol.md
- Maquina de estados: ../../kernel/state-machine.md
- Estado: ../../templates/project-state.md
- Runner: ../../skills/workflow-runner/SKILL.md

## Exemplos de uso

- Codex: `$framework-next Retome este projeto pelo estado persistente.`
- Claude Code: `/framework-next Determine a proxima operacao sem usar a conversa anterior.`
