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

3. **Plan and schedule**
   - crie tarefas pequenas com dependencias;
   - classifique write scopes e recursos compartilhados;
   - defina quais podem rodar em paralelo;
   - use `worktree-lane-manager` para writers independentes;
   - escolha o bundle de skills de cada role;
   - mantenha uma fila de trabalho elegivel alem da tarefa atualmente visivel.

4. **Reset and dispatch developer lanes**
   - antes de task nova, persista o resultado anterior e use
     `fresh-task-session`;
   - resete o contexto do agente ou abra sessao nova; `clear` do shell sozinho
     nao conta como reset;
   - gere `agent-dispatch`;
   - inclua task contract, read-first, allowed files, acceptance, tests e
     workspace/lane;
   - envie somente contexto relevante para economizar tokens;
   - limite autoridade a `local_only` por default;
   - writers paralelos usam branches/worktrees distintas e scopes disjuntos.

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

8. **Integrate / batch**
   - rode goal coverage/verificacao aplicavel;
   - use `git-decision-router` e gates existentes;
   - se houver 2+ PRs abertos, crie/atualize o registro de
     `integration-batch-manager`;
   - monte a composicao executavel dos candidatos compativeis e valide a arvore
     combinada antes dos merges quando isso reduzir CI/latencia;
   - integre somente com aceite e evidencias suficientes;
   - required checks/branch protection de cada PR continuam valendo.

9. **Continue**
   - selecione todas as proximas tarefas elegiveis, nao apenas uma;
   - preencha lanes independentes quando nao houver conflito;
   - se uma tarefa precisar do usuario, use
     `decision-pause-and-continue.md`, registre `Q-###` e deixe-a
     `awaiting_decision`;
   - continue outra tarefa da fase ou outra spec/fase ja aprovada quando suas
     dependencias estiverem satisfeitas;
   - finalize apenas quando o objetivo global estiver coberto.

## Paralelismo seguro

O default e ocupar capacidade disponivel quando o trabalho for realmente
independente:

- cada writer usa branch + worktree propria;
- `allowed_files`/write scopes devem ser disjuntos;
- dependencia entre tasks serializa as lanes afetadas;
- schema/migration/lockfile/config central podem exigir serializacao;
- tester pode preparar estrategia antes do diff e validar depois;
- reviewer so revisa resultado materializado e nunca o proprio trabalho;
- pesquisa/analise read-only pode ocorrer em paralelo sem worktree exclusiva.

O runtime legado nao possui multi-claim canonico. Enquanto isso, a camada de
orquestracao mantem os claims por dispatch/lane e serializa as transicoes formais
do kernel na integracao. Isso nao autoriza dois workers a editar o mesmo escopo.

## Stop conditions

O orquestrador para o dispatch afetado quando houver:

- decisao `user_required` para aquele dispatch;
- conflito de escopo/arquivos;
- dependencia nao satisfeita;
- teste obrigatorio falhando sem correcao autorizada;
- requisito contraditorio;
- mudanca destrutiva/externa nao autorizada;
- estado Git inseguro.

Nao pare todo o time se outras tarefas independentes ainda puderem avancar.
Registre a pergunta no notebook, preserve a lane bloqueada e recalcule o
scheduler imediatamente.

## Contexto e tokens

Cada mudanca de task id deve preferir uma sessao limpa. O orquestrador persiste o
que importa, descarta conversa concluida e manda o dispatch minimo. Reutilizar
contexto longo entre tarefas independentes e excecao, nao default.

## Integration batches

Com 2 ou mais PRs abertos, o orquestrador sempre mantem um batch inventory. PRs
integration-ready e compativeis entram numa branch/worktree efemera; a CI da
uniao dos impactos valida conflitos/regressoes combinados. Drafts/incompativeis
ficam registrados com motivo. O batch nunca substitui checks que a protecao do
repositorio exige especificamente em cada PR.
