# Migracao para o Kernel Persistente

## Escopo

Esta migracao cobre P0 (kernel/estado) e P1 (disciplina de execucao). Ela nao
introduz registry global, packs, reorganizacao ampla de skills ou P2/P3.

## Compatibilidade

- Skills, workflows, rubrics e templates publicos existentes nao foram removidos
  nem renomeados.
- `workflow-orchestrator` permanece como alias e encaminha planejamento para
  `workflow-planner` e execucao para `workflow-runner`.
- Entradas antigas continuam aceitas como contexto opcional, mas nao substituem
  estado ou evidencia persistente.
- Projetos sem `.agent/` continuam funcionando no modo anterior. Inicializacao
  exige comando explicito e nunca sobrescreve uma pasta existente.
- Estados P0/P1 sem `execution_mode` usam `critical` como default compativel.
- Novas tarefas nao herdam automaticamente o kernel apenas porque `.agent/`
  existe; o router seleciona `fast`, `standard` ou `critical`.
- Persistencia `standard` cria somente `STATE.md` e `PLAN.md`; `fast` nao
  inicializa `.agent/`.
- Novos campos de templates nao invalidam documentos antigos; ao entrar no
  kernel, o projeto deve inicializar ou migrar seu `STATE.md` para schema 1.
- `git.worktree` com caminho absoluto e formato legado: continua carregando em
  qualquer maquina e nao invalida o projeto.

## Migrar `git.worktree` para o formato portatil

Kernels antigos gravavam o caminho absoluto do clone local:

```json
"worktree": "/Users/voce/dev/projeto"
```

Isso quebrava ao trocar de computador. O formato portatil e:

```json
"worktree": "."
```

`.` significa a raiz do repositorio Git que contem `.agent/`. A raiz absoluta e
descoberta em runtime por `git rev-parse --show-toplevel`.

Comportamento durante a migracao:

- validar um estado legado nao modifica o arquivo e nao falha; emite o aviso
  `git-worktree-legacy` com a acao corretiva;
- a identidade do repositorio deixa de depender do caminho absoluto e passa a
  ser provada por Git mais a localizacao real de `.agent/`;
- a conversao e uma operacao explicita.

```bash
./scripts/framework-next normalize-worktree --project <repo> --check
./scripts/framework-next normalize-worktree --project <repo>
```

A operacao altera somente a linha `worktree`, preserva o resto do arquivo byte a
byte, e idempotente, nunca substitui um caminho absoluto por outro e recusa
executar fora de um repositorio que comprovadamente possua `.agent/`.

Commite o resultado uma vez; os demais computadores recebem o estado ja portatil
e nao produzem diff.

## Mudanca deliberadamente mais estrita

O kernel bloqueia comportamentos que o fluxo anterior podia deixar implícitos:

- tarefa ativa sem contrato integral;
- arquivo fora de `allowed_files`;
- teste alegado sem comando/resultado;
- tarefa concluida sem evidencia por criterio;
- review baseado somente no resumo do implementador;
- autoaprovacao;
- plan change sem decisao e novo gate;
- `ready_to_ship` com blocker ou waiver invalido;
- contexto stale ou referencia ausente.

Nao ha alias para contornar esses guards.

## Adotar em um projeto existente

1. Garanta working tree compreendido e registre o commit atual.
2. Confirme que a tarefa exige `critical` e rode
   `scripts/framework-next init --project <repo> --name <nome> --mode critical`.
3. Preencha `PROJECT.md`, `CONTEXT.md`, `REQUIREMENTS.md` e `ROADMAP.md`.
4. Crie a fase com `init-phase`.
5. Congele `SPEC.md`; gere `PLAN.md` e contratos completos em `TASKS.md`.
6. Rode `plan-quality-checker` e registre o gate.
7. Use `framework-next` para obter a unica operacao seguinte.

Nao copie resumos longos para `STATE.md`; use os artefatos referenciados.

## Instalacao

Os installers continuam preservando skills externas. Para que referências
relativas funcionem, eles também sincronizam arquivos do framework em:

```text
<tool-root>/kernel
<tool-root>/workflows
<tool-root>/rubrics
<tool-root>/templates
<tool-root>/docs
<tool-root>/scripts
<tool-root>/installers
```

Arquivos externos não presentes na fonte não são removidos. Arquivos de mesmo
nome são copiados para o backup da execução antes da substituição.

## Verificacao

```bash
bash installers/verify-framework.sh
python3 -m unittest discover -s tests -v
make security:check
```
