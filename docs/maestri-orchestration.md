# Maestri Multi-Agent Orchestration

## Objetivo

Usar o Agent Framework como sistema operacional de um time de agentes dentro do
Maestri, em vez de apenas como conjunto de skills que um unico agente executa.

Configuracao recomendada:

| Lane | Papel | Responsabilidade |
| --- | --- | --- |
| Orchestrator | control plane | spec, plano, dispatch, decisoes, roteamento e integracao |
| Dev | developer | implementar o escopo autorizado |
| Test | tester | estrategia, testes, regressao e runtime QA |
| Review | reviewer | spec compliance, qualidade e findings independentes |

Os modelos podem variar por lane. O papel e o contrato importam mais que o
provider.

## O problema atual do framework

O framework ja tem planner, runner, task runner, reviewers, contratos, memoria,
evidence e `parallel_group`. Mas o fluxo principal ainda assume uma unica tarefa
ativa coordenada pelo runner, e o antigo `workflow-orchestrator` virou apenas um
alias de compatibilidade.

Isso funciona muito bem para um unico agente disciplinado, mas nao explora um
ambiente onde um orquestrador consegue conversar com varios terminais
especializados.

## V1 — utilizavel agora

A V1 e baseada em protocolo e artefatos, sem depender de uma reescrita imediata
do kernel.

Novos assets:

- `skills/team-orchestrator`
- `skills/decision-authority-router`
- `skills/project-notebook`
- `skills/worktree-lane-manager`
- `skills/fresh-task-session`
- `skills/integration-batch-manager`
- `workflows/multi-agent-development.md`
- `workflows/decision-pause-and-continue.md`
- `workflows/integration-batch.md`
- `kernel/orchestration-policy.md`
- `kernel/context-budget-policy.md`
- `templates/agent-dispatch.md`
- `templates/orchestration-state.md`
- `templates/project-notes/*`
- `templates/integration-batch.md`

### Ciclo

1. O orquestrador entende o pedido e cria/refina spec.
2. Planeja tarefas e dependencias.
3. Gera um dispatch fechado para o Dev.
4. O Dev implementa e devolve resultado.
5. O Testador valida e devolve evidencia.
6. O Revisor inspeciona spec + diff + testes.
7. Finding real volta ao Dev.
8. Quando passa, o orquestrador integra e escolhe a proxima tarefa.
9. O ciclo continua sem pedir permissao para detalhes locais.

## Worktrees e paralelismo

Quando duas tarefas escreviveis forem independentes, o orquestrador deve usar
branches/worktrees separadas e manter lanes simultaneas. Dependencia, overlap de
arquivos, migration/schema, lockfile ou contrato compartilhado podem serializar
as lanes.

Se uma lane ficar aguardando uma decisao sua, ela preserva sua worktree e o
scheduler procura outro trabalho independente — inclusive outra spec/fase ja
aprovada.

## Notebook do projeto

Projetos multiagente ganham:

```text
.agent/notes/
  INDEX.md
  QUESTIONS.md
  PROGRESS.md
  PHASES.md
```

`QUESTIONS.md` funciona como sua caixa de decisoes. Uma pergunta `Q-###`
registra contexto, opcoes, recomendacao, o que esta bloqueado e o que pode
continuar. Quando voce responde, ela aponta para a decisao formal em
`DECISIONS.md` e a task volta para a fila.

`PROGRESS.md` explica o que foi feito; `PHASES.md` resume cada fase/spec
implementada; `INDEX.md` mostra lanes, perguntas, ultima entrega e proximo
trabalho.

## Sessao limpa e economia de tokens

Toda task nova prefere contexto novo. Antes de reutilizar uma lane, o
orquestrador persiste o resultado anterior, reseta a sessao do agente (ou abre
uma nova), limpa o terminal visual e manda somente o dispatch necessario.

`clear` no shell sozinho nao reduz tokens. A economia real vem de nao carregar
conversas antigas, logs completos, skills irrelevantes ou historico de fases ja
persistido.

## Integration batch

Com 2+ PRs abertos, existe um batch inventory. Heads compativeis e prontos para
integracao sao combinados numa branch/worktree efemera e recebem CI da arvore
combinada. Se o CI depende de evento de PR, o orquestrador pode abrir um batch PR
efemero.

O batch agiliza validacao combinada, mas nao ignora required checks ou branch
protection dos PRs reais.

## O que vira decisao

A nova politica separa tres classes:

### local

Nao precisa ser salvo como decisao de projeto e nao deve interromper o usuario.

Exemplos:

- nome de helper;
- organizacao interna equivalente;
- formato de fixture;
- pequena refatoracao dentro do contrato;
- escolha entre duas implementacoes equivalentes e facilmente reversiveis.

### record

O orquestrador pode decidir e salvar porque vale lembrar depois, mas nao precisa
perguntar ao usuario.

Exemplos:

- boundary interna entre modulos;
- estrategia de retry dentro de uma integracao ja aprovada;
- convencao arquitetural nova, reversivel e alinhada ao objetivo.

### user_required

O orquestrador pergunta porque muda um compromisso relevante.

Exemplos:

- comportamento/UX nao especificado;
- API publica;
- schema/dados destrutivos;
- auth/security/privacy;
- provider/custo novo;
- deploy/producao;
- segredo;
- lock-in arquitetural relevante;
- requisitos conflitantes.

## Como o dispatch reduz ruido

Em vez de dizer ao Dev "leia o projeto e implemente", o orquestrador envia:

- objetivo;
- task/spec relevante;
- skills exatas;
- workflow exato;
- arquivos para ler;
- arquivos permitidos;
- o que nao pode mudar;
- acceptance criteria;
- testes;
- autoridade de decisao;
- quando parar;
- formato do resultado.

Isso deixa cada terminal mais previsivel e reduz contexto desnecessario.

## V2 — runtime multi-claim

Depois da V1 estabilizada, o kernel deve ganhar suporte real a varias tarefas
ativas.

Proposta:

- substituir o unico `current_task` por claims ativos por task/agent;
- lease por dispatch;
- branch/worktree por writer;
- lock de write-scope derivado de `allowed_files`;
- estados de dispatch no runtime;
- heartbeats/timeout de worker;
- `parallel_group` realmente executavel;
- eventos append-only de dispatch/result/reassignment;
- comandos como `dispatch`, `claim`, `submit-result`, `accept-result`,
  `reassign` e `cancel-dispatch`.

O orquestrador continua unico. O que fica paralelo sao os workers.

## V3 — scheduler autonomo

Com multi-claim validado, o orquestrador pode preencher lanes automaticamente:

- Dev recebe a proxima tarefa escrevivel elegivel;
- Test recebe estrategia ou verificacao pendente;
- Review recebe resultado pronto e independente;
- especialistas sao criados sob demanda;
- bloqueio de uma lane nao congela trabalho independente;
- so uma decisao `user_required` realmente interrompe o usuario.

Esse e o ponto em que o Agent Framework passa de "framework para agentes" para
"framework para gerir uma equipe de agentes".
