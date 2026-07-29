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
3. Inicialize somente com pedido/necessidade confirmada. Para o kernel completo:
   `scripts/framework-next init --project <caminho> --name <nome> --mode critical`.
   Para retomada leve justificada:
   `scripts/framework-next init --project <caminho> --name <nome> --mode standard`,
   que cria somente `STATE.md` e `PLAN.md`.
4. Leia `execution_mode`; estado antigo sem o campo usa `critical` por
   compatibilidade segura.
5. Em `standard`, leia apenas `STATE.md`/`PLAN.md` existentes e coordene o plano
   leve sem exigir seal, contratos, ledger ou reviewers separados.
6. Em `critical`, leia todos os artefatos ativos, valide referencias/contexto/Git
   e siga exatamente a operacao retornada.
7. Use transicoes formais somente no lifecycle `critical`, depois da evidencia.

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
- Estado inconsistente bloqueia execucao.
- Nenhuma transicao proibida ou artefato ausente e inferido.
- Ausencia de `.agent/` roteia para `auto`/`fast`, sem criar arquivos.
- Estado P0/P1 antigo continua como `critical`.

## Arquivos de apoio

- Protocolo: ../../kernel/protocol.md
- Maquina de estados: ../../kernel/state-machine.md
- Estado: ../../templates/project-state.md
- Runner: ../../skills/workflow-runner/SKILL.md

## Exemplos de uso

- Codex: `$framework-next Retome este projeto pelo estado persistente.`
- Claude Code: `/framework-next Determine a proxima operacao sem usar a conversa anterior.`
