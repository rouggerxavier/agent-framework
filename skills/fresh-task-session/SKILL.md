---
name: fresh-task-session
description: Prepara uma lane para tarefa nova salvando o resultado anterior, resetando a sessao/contexto quando possivel e enviando somente o dispatch minimo.
---

# Fresh Task Session

## Objetivo

Comecar cada tarefa nova com contexto limpo e barato, evitando que um worker
carregue raciocinio, logs e instrucoes de tarefas anteriores.

## Quando usar

- Antes de qualquer dispatch com novo `task_id`.
- Ao mudar a role da lane.
- Ao mudar de spec/fase.
- Quando o contexto anterior ficou grande, ruidoso ou contraditorio.
- Depois de uma tarefa encerrada, bloqueada ou pausada por decisao se a lane for
  reutilizada para outro trabalho.

## Workflow

1. Confirme que o resultado da tarefa anterior foi persistido.
2. Registre branch/worktree, testes, findings, decisoes e pergunta pendente quando
   houver.
3. Atualize notebook e estado de orquestracao.
4. Resete a sessao do agente usando a primitiva do harness/Maestri.
5. Se reset de contexto nao existir, abra uma sessao/terminal novo.
6. Limpe o terminal visual apenas como higiene; nao conte isso como reset de
   contexto.
7. Envie o novo `agent-dispatch` e somente os artefatos aplicaveis.
8. O worker confirma task id, lane/worktree e write scope antes de editar.

## Criterios de aceite

- Nenhum resultado importante ficou apenas no contexto descartado.
- A nova tarefa nao recebe conversa inteira da anterior.
- O prompt novo contem somente contexto relevante.
- Troca de tarefa nao depende de `clear` de shell para economizar tokens.

## Arquivos de apoio

- Politica: ../../kernel/context-budget-policy.md
- Dispatch: ../../templates/agent-dispatch.md
- Notebook: ../project-notebook/SKILL.md
- Compressor: ../context-compressor/SKILL.md
