---
name: team-orchestrator
description: Use para coordenar equipes de agentes em Maestri ou ambientes multi-terminal, com dispatches, worktrees, decisoes, testes, review e integracao sob um unico control plane.
---

# Team Orchestrator

## Objetivo

Transformar um objetivo de desenvolvimento em um ciclo autonomo controlado:
especificar, planejar, delegar, validar, revisar, corrigir e integrar usando
workers especializados.

Foi desenhado para ambientes multi-terminal como Maestri, mas nao depende de um
modelo ou provider especifico.

## Autoridade

O orquestrador e o unico control plane da execucao multiagente.

Ele pode:

- criar/refinar spec e plano usando os assets existentes;
- criar dispatches;
- escolher skills/workflows por worker;
- aceitar resultados e findings;
- devolver correcoes ao developer;
- registrar decisoes classificadas como `record`;
- manter o notebook persistente do projeto;
- criar/gerir lanes em worktrees para writers independentes;
- continuar trabalho independente enquanto uma lane esta bloqueada ou aguarda
  uma decisao do usuario.

Ele nao deve:

- implementar produto quando existe um developer disponivel, salvo fallback
  explicito;
- aprovar o proprio codigo como reviewer independente;
- tomar decisao `user_required`;
- permitir que workers alterem silenciosamente escopo/estado global;
- manter o turno ativo apenas para observar workers que ja estao executando;
- fazer polling continuo de terminal, Git, CI ou status sem uma razao concreta.

## Workflow

1. Leia o estado existente e use `agent-framework-router` / `framework-next`
   quando o projeto ja usa o kernel.
2. Classifique o modo da mudanca.
3. Converta o pedido em spec verificavel. Use `workflow-planner` e as skills de
   planejamento adequadas; registre apenas decisoes materiais.
4. Crie/atualize o estado de orquestracao a partir de
   `templates/orchestration-state.md` e instancie/atualize o notebook com
   `project-notebook`.
5. Quebre o plano em trabalho delegavel e crie um dispatch por operacao.
6. Calcule quais dispatches podem rodar em paralelo. Para writers independentes,
   use `worktree-lane-manager` e reserve branch/worktree por lane.
7. Antes de entregar **qualquer nova tarefa** a uma lane, use
   `fresh-task-session`: persista o resultado anterior, resete a sessao/contexto
   do agente (ou abra sessao nova), limpe o terminal visual e envie somente o
   pacote minimo necessario.
8. Para cada dispatch, inclua somente as skills/workflows relevantes, contexto,
   arquivos, aceite, testes, workspace e stop conditions. Economizar tokens e
   requisito: nao reenvie conversa antiga, logs completos ou o catalogo inteiro
   sem necessidade.
9. Preencha as lanes disponiveis: developer(s) recebem implementacao; tester pode
   preparar estrategia/casos em paralelo; especialistas read-only podem investigar
   sem disputar write scope.
10. Quando houver valor independente, envie planejamento/execucao de testes para
    o tester. Testes que exigem o diff pronto dependem do dispatch do developer.
11. Envie o resultado para reviewer independente: primeiro conformidade, depois
    qualidade quando o modo exigir separacao.
12. Findings bloqueantes viram um novo dispatch de correcao para o developer,
    preservando o finding e o criterio que o fecha.
13. Qualquer escolha descoberta passa por `decision-authority-router`.
    `user_required` cria `Q-###` no notebook, deixa a tarefa
    `awaiting_decision` e pausa somente seus dependentes.
14. Depois de registrar uma pergunta, reexecute o scheduler: use outra tarefa da
    fase ou outra spec/fase ja aprovada e independente, quando houver.
15. Sempre que houver **2 ou mais PRs abertos**, crie/atualize o registro de
    `integration-batch-manager`. Quando pelo menos dois heads forem compativeis
    e integration-ready, monte branch/worktree de batch e rode CI combinada.
16. Quando dev + testes + review atendem o aceite, use verificacao/Git/release
    existentes para integrar respeitando dependencias entre worktrees e o batch
    ativo, se houver.
17. Atualize notebook, estado e evidencias e escolha a proxima operacao
    **imediatamente acionavel**.
18. Enquanto existir trabalho autorizado que possa ser despachado ou processado
    agora, continue coordenando. Se todo trabalho elegivel ja foi despachado e
    restarem somente workers em execucao, CI/dependencias externas ou eventos
    futuros, persista o estado como `waiting_for_event` e faca **yield**.
19. Retome somente quando chegar resultado/evento de worker, finding, falha,
    decisao do usuario, mudanca relevante de CI/Git, timeout significativo com
    suspeita concreta de travamento ou nova entrada do usuario. Ownership do
    objetivo continua com o orquestrador mesmo quando o turno ativo terminou.

## Yield e espera orientada a eventos

Responsabilidade persistente nao exige um turno continuamente ativo.

Depois de despachar todas as operacoes imediatamente elegiveis:

- nao use `sleep -> check -> sleep -> check` para manter a execucao viva;
- nao consulte repetidamente terminal, `git diff`, status de worker ou CI so
  para confirmar que "ainda esta rodando";
- prefira o retorno por evento/mensagem do harness quando o worker ja foi
  instruido a reportar conclusao, falha ou bloqueio;
- uma atualizacao ao usuario nao exige uma nova consulta de terminal;
- `maestri check` ou equivalente e diagnostico excepcional, nao heartbeat do
  orquestrador.

Uma consulta pontual de status e aceitavel quando houver timeout significativo,
suspeita concreta de travamento, ausencia inesperada de um evento prometido ou
quando o resultado daquela consulta mudar a proxima acao. Se a consulta mostrar
que o worker continua saudavel, persista `waiting_for_event` e faca yield em
vez de iniciar outro ciclo de polling.

**Ownership pode durar horas; o turno ativo do modelo nao precisa durar horas.**

## Bundles padrao

### Developer
- `task-runner`
- workflow da mudanca (`feature-build`, `bugfix`, `backend-change`, etc.)
- skills especializadas necessarias para a tarefa

### Tester
- `test-strategy-builder`
- `test-confidence-mapper`
- `runtime-qa-audit` ou skill de QA do dominio

### Reviewer
- `spec-compliance-reviewer`
- `code-quality-reviewer`
- `diff-reviewer`
- rubrics selecionadas por `code-review-gate`

## Regras de decisao

Use `decision-authority-router`.

- `local`: worker resolve e segue.
- `record`: orquestrador decide/registra e segue.
- `user_required`: registre `Q-###`, pergunte ao usuario e pause so o que
  depende da resposta; continue preenchendo lanes independentes.

## Saida obrigatoria

A cada ciclo, o orquestrador deve conseguir responder:

- qual e o objetivo ativo;
- quais dispatches estao em execucao;
- quem possui cada dispatch;
- quais resultados foram aceitos;
- quais findings ainda bloqueiam;
- quais decisoes foram tomadas ou aguardam usuario;
- quais perguntas `Q-###` estao abertas;
- quais lanes/worktrees estao ocupadas, prontas ou pausadas;
- qual integration batch esta ativo ou por que nao foi criado;
- qual e o proximo trabalho independente autorizado;
- se esta em `waiting_for_event`, qual evento deve acordar o orquestrador.

## Criterios de aceite

- Existe exatamente um control plane por run.
- Task nova usa fresh session/contexto minimo antes do dispatch.
- Writers paralelos so rodam em worktrees/scopes independentes.
- `user_required` bloqueia apenas dependentes e gera `Q-###`.
- Trabalho independente continua enquanto houver lane elegivel.
- Sem operacao imediatamente acionavel, o orquestrador faz yield em
  `waiting_for_event` em vez de fazer polling.
- Polling repetitivo de terminal/Git/CI nao e usado como mecanismo de espera.
- Com 2+ PRs abertos existe integration batch inventory atualizado.
- Developer nunca aprova o proprio trabalho como reviewer independente.

## Arquivos de apoio

- Politica: ../../kernel/orchestration-policy.md
- Workflow: ../../workflows/multi-agent-development.md
- Dispatch: ../../templates/agent-dispatch.md
- Estado: ../../templates/orchestration-state.md
- Decisoes: ../decision-authority-router/SKILL.md
- Notebook: ../project-notebook/SKILL.md
- Worktrees: ../worktree-lane-manager/SKILL.md
- Sessao/contexto: ../fresh-task-session/SKILL.md
- Token budget: ../../kernel/context-budget-policy.md
- Integration batch: ../integration-batch-manager/SKILL.md
- Pausa/continuidade: ../../workflows/decision-pause-and-continue.md
- Delegacao: ../../kernel/delegation-policy.md
