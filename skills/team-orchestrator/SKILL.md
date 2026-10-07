---
name: team-orchestrator
description: Coordena uma equipe de agentes de desenvolvimento, testes e review por dispatches, mantendo um unico control plane e escalando apenas decisoes materiais.
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
- continuar trabalho independente enquanto uma lane esta bloqueada.

Ele nao deve:

- implementar produto quando existe um developer disponivel, salvo fallback
  explicito;
- aprovar o proprio codigo como reviewer independente;
- tomar decisao `user_required`;
- permitir que workers alterem silenciosamente escopo/estado global.

## Workflow

1. Leia o estado existente e use `agent-framework-router` / `framework-next`
   quando o projeto ja usa o kernel.
2. Classifique o modo da mudanca.
3. Converta o pedido em spec verificavel. Use `workflow-planner` e as skills de
   planejamento adequadas; registre apenas decisoes materiais.
4. Crie/atualize o estado de orquestracao a partir de
   `templates/orchestration-state.md`.
5. Quebre o plano em trabalho delegavel e crie um dispatch por operacao.
6. Para cada dispatch, inclua somente as skills/workflows relevantes, contexto,
   arquivos, aceite, testes e stop conditions.
7. Envie implementacao para o developer.
8. Quando houver valor independente, envie planejamento/execucao de testes para
   o tester. Testes que exigem o diff pronto dependem do dispatch do developer.
9. Envie o resultado para reviewer independente: primeiro conformidade, depois
   qualidade quando o modo exigir separacao.
10. Findings bloqueantes viram um novo dispatch de correcao para o developer,
    preservando o finding e o criterio que o fecha.
11. Qualquer escolha descoberta passa por `decision-authority-router`.
12. Quando dev + testes + review atendem o aceite, use verificacao/Git/release
    existentes para integrar.
13. Atualize o estado, registre evidencias e escolha a proxima operacao. Continue
    o ciclo ate concluir, bloquear ou precisar do usuario.

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
- `user_required`: pergunta ao usuario e pausa so o que depende da resposta.

## Saida obrigatoria

A cada ciclo, o orquestrador deve conseguir responder:

- qual e o objetivo ativo;
- quais dispatches estao em execucao;
- quem possui cada dispatch;
- quais resultados foram aceitos;
- quais findings ainda bloqueiam;
- quais decisoes foram tomadas ou aguardam usuario;
- qual e a proxima operacao autorizada.

## Arquivos de apoio

- Politica: ../../kernel/orchestration-policy.md
- Workflow: ../../workflows/multi-agent-development.md
- Dispatch: ../../templates/agent-dispatch.md
- Estado: ../../templates/orchestration-state.md
- Decisoes: ../decision-authority-router/SKILL.md
- Delegacao: ../../kernel/delegation-policy.md
