# Task Start Workflow

Use para iniciar formalmente a primeira ou a proxima tarefa de uma fase ja
planejada e selada.

## Quando usar

- `next_action` e `execute-task -> <ID>`.
- O plano da fase esta selado.
- A tarefa alvo esta `pending` e com dependencias satisfeitas.

## Quando nao usar

- Fase ainda nao selada: use `seal-plan` e `transition --to planned`.
- Tarefa ja `executing`: use `resume-task`; o binding ja existe.
- Fase ainda nao ativa: veja `workflows/phase-rotation.md`.

## Sequencia

1. Confirme a operacao com `framework-next validate` e o `next_action`.
2. **Crie ou entre na branch de trabalho.** Nao inicie na branch de integracao:

```bash
git switch -c feat/<slug-da-tarefa>
```

3. Inicie a tarefa:

```bash
framework-next start-task \
  --actor workflow-runner \
  --reason "Plan gate passed and <ID> is eligible"
```

`--task-id <ID>` e opcional e serve so como confirmacao: se nao for igual a
tarefa que o kernel selecionou, o comando recusa. **O alvo vem do kernel, nao
do operador** — nao existe `select-task`.

4. Rode `validate` e confirme `state: valid`.

## O que o inicio faz

Numa unica operacao: seleciona a tarefa elegivel em `current_task`, move a
tarefa e a fase para `executing`, grava o binding e registra o evento no ledger
da fase.

`current_task.execution` recebe a branch lida do Git, o id da tarefa, o valor
portatil de worktree, timestamp e actor. **Nao existe argumento de branch em
nenhum comando** — o binding e capturado, nunca declarado, entao ele nao pode
nomear uma branch que nao esta em uso.

`task-status` **nao** seleciona tarefa e `transition` **nao** inventa
`current_task`; ambos continuam operando sobre uma tarefa ja selecionada.
`reconcile-phase` e reconciliacao retrospectiva e nao deve ser usada para
iniciar trabalho. Nenhum hand-edit de `STATE.md` e necessario.

## Pre-condicoes que recusam

- `HEAD` destacado — nao ha branch a vincular;
- branch atual igual a `git.base_branch` — a branch de integracao e onde o
  trabalho chega, nao onde e escrito;
- nenhuma tarefa selecionada em `current_task.id`;
- contrato invalido, dependencia insatisfeita, plano nao selado, risco nao
  classificado ou worktree suja sem worktree isolada;
- fase fora de `planned`;
- outra tarefa ja em `executing`, `reviewing` ou `verifying`;
- `--task-id` diferente da tarefa selecionada pelo kernel.

Recusa nao escreve nada: estado, indice e ledger ficam intactos. Os tres
documentos se movem juntos — falha em qualquer etapa, inclusive no ledger,
restaura `STATE.md` e `TASKS.md` como estavam.

Repetir o mesmo `start-task` e no-op. Repetir para outra tarefa, outra branch ou
outro worktree e recusado.

## Durante a execucao

Enquanto a tarefa estiver em `executing`, `reviewing` ou `verifying`, trocar de
branch e erro. Se acontecer, o kernel devolve `restore-execution-branch` com a
branch correta — a correcao e um `git switch`, nunca uma edicao de `STATE.md`.

```bash
git switch <branch-vinculada>
```

## Ao encerrar

Sair dos estados de execucao libera o binding para `git.last_execution`, que e
historico e nunca e validado. A branch pode ser mergeada e apagada, e a branch
de integracao continua valida. A proxima tarefa cria o seu proprio binding ao
comecar.

## Saidas

- Tarefa em `executing`, vinculada a branch real.
- `validate` limpo.
- Proxima operacao calculada pelo kernel.
