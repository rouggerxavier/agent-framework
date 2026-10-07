# Multi-Agent Development Workflow

Use quando um orquestrador coordena developer, tester e reviewer como workers
separados.

## Objetivo

Automatizar o ciclo de desenvolvimento sem transformar todos os agentes em
orquestradores concorrentes.

```text
User goal
  -> Orchestrator
     -> Spec / Plan
     -> Dispatch developer
        -> implementation result
     -> Dispatch tester
        -> test evidence
     -> Dispatch reviewer
        -> findings / approval
     -> corrections when needed
     -> verify / integrate
     -> next task
```

## Regras centrais

- Um unico control plane: `team-orchestrator`.
- Cada worker recebe um dispatch fechado.
- Workers recebem skills/workflows selecionados, nao o catalogo inteiro.
- O orquestrador e dono de spec, plano, fila, decisoes e roteamento.
- Developer nao aprova o proprio trabalho.
- Tester e reviewer nao expandem escopo.
- Toda escolha nova passa pelo `decision-authority-router`.
- Pergunte ao usuario apenas por `user_required`.

## Sequencia

1. **Ground**
   - leia repo, estado e docs relevantes;
   - recupere decisoes aceitas;
   - identifique objetivo, restricoes e criterios de done.

2. **Specify**
   - use `workflow-planner` e skills de spec;
   - transforme comportamento ambiguo em aceite verificavel;
   - classifique lacunas com `decision-authority-router`.

3. **Plan**
   - crie tarefas pequenas com dependencias;
   - defina quais podem ser lidas/testadas em paralelo;
   - escolha o bundle de skills de cada role.

4. **Dispatch developer**
   - gere `agent-dispatch`;
   - inclua task contract, read-first, allowed files, acceptance e tests;
   - limite autoridade a `local_only` por default.

5. **Dispatch tester**
   - antes do codigo: pode produzir estrategia, casos e gaps;
   - depois do codigo: roda testes, regressao e runtime checks;
   - nao corrige produto; retorna evidencias/falhas.

6. **Dispatch reviewer**
   - deve inspecionar diff e evidencias diretamente;
   - em critical: spec compliance e code quality preservam independencia;
   - findings bloqueantes retornam ao developer como dispatch de correcao.

7. **Resolve loop**
   - developer corrige somente findings aceitos;
   - tester reexecuta verificacoes afetadas;
   - reviewer reavalia apenas diff/criterios invalidados;
   - repita ate passar ou bloquear.

8. **Integrate**
   - rode goal coverage/verificacao aplicavel;
   - use `git-decision-router` e gates existentes;
   - integre somente com aceite e evidencias suficientes.

9. **Continue**
   - selecione proxima tarefa elegivel;
   - mantenha workers independentes ocupados quando nao houver conflito;
   - finalize apenas quando o objetivo global estiver coberto.

## Paralelismo seguro

A V1 prioriza seguranca:

- um writer de produto por escopo;
- tester pode trabalhar em estrategia antes do diff;
- reviewer pode revisar apenas depois de resultado implementado;
- pesquisa/analise read-only pode ocorrer em paralelo;
- dois writers so quando worktrees e allowed_files forem disjuntos.

O suporte de kernel a multiplos claims ativos deve ser implementado antes de
tratar paralelismo de writers como garantia formal.

## Stop conditions

O orquestrador para o dispatch afetado quando houver:

- decisao `user_required`;
- conflito de escopo/arquivos;
- dependencia nao satisfeita;
- teste obrigatorio falhando sem correcao autorizada;
- requisito contraditorio;
- mudanca destrutiva/externa nao autorizada;
- estado Git inseguro.

Nao pare todo o time se outras tarefas independentes ainda puderem avancar.
