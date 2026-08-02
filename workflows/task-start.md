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

3. Inicie a tarefa. A branch e capturada automaticamente:

```bash
framework-next transition --to executing \
  --actor workflow-runner \
  --reason "Plan gate passed and <ID> is eligible"
```

4. Rode `validate` e confirme `state: valid`.

## O que o inicio grava

`current_task.execution`, com a branch lida do Git, o id da tarefa, o valor
portatil de worktree, timestamp e actor. **Nao existe argumento de branch em
nenhum comando** — o binding e capturado, nunca declarado, entao ele nao pode
nomear uma branch que nao esta em uso.

## Pre-condicoes que recusam

- `HEAD` destacado — nao ha branch a vincular;
- branch atual igual a `git.base_branch` — a branch de integracao e onde o
  trabalho chega, nao onde e escrito;
- nenhuma tarefa selecionada em `current_task.id`;
- contrato invalido, dependencia insatisfeita, plano nao selado, risco nao
  classificado ou worktree suja sem worktree isolada.

Recusa nao escreve nada: estado e indice ficam intactos.

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
