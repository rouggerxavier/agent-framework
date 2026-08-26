# agent-framework

Framework pessoal e versionavel de skills, rubrics, workflows, templates e docs
para Codex e Claude Code.

## Objetivo

Manter `~/agent-framework` como fonte principal das suas skills reutilizaveis. Os installers sincronizam essas skills para:

- Codex: `~/.agents/skills`
- Claude Code: `~/.claude/skills`

O framework e seguro para Git privado quando usado sem secrets, tokens, senhas, `.env`, chaves privadas ou dados sensiveis.

## Estrutura

```text
agent-framework/
  README.md
  .gitignore
  kernel/
  skills/
  rubrics/
  workflows/
  templates/
  installers/
  docs/
  scripts/
  tests/
```

## Execucao adaptativa

```text
Fast otimiza a velocidade.
Standard organiza o desenvolvimento normal.
Critical protege a aplicacao contra danos graves.
```

O framework seleciona uma de tres rotas:

```text
Dano grave se falhar        → critical
Curto, contido, baixo impacto → fast
O resto                      → standard
```

| Modo | Fluxo | Governanca |
| --- | --- | --- |
| `fast` | inspect → implement → targeted verification → diff review | sem `.agent/`, spec, contrato, seal, ledger, reviewers separados ou worktree |
| `standard` | focused grounding → short plan → implement → tests → integrated review | estado opcional, uma review integrada, sem seal nem reviews separadas |
| `critical` | lifecycle persistente completo | P0/P1 integral, duas reviews independentes |

Calibracao esperada, como referencia e nao como cota: `fast` ~30%, `standard`
~65-70%, `critical` ~1-5%.

Use o router como entrada de uma tarefa nova:

```text
$agent-framework-router --fast
Corrija o typo no titulo da pagina.
```

```text
$agent-framework-router --standard
Implemente o novo endpoint e os testes.
```

```text
$agent-framework-router --critical
Troque o gateway de pagamento do checkout.
```

`--auto` (ou nenhuma flag) deixa o router decidir, e o padrao e `standard`.
`fast` exige evidencia positiva de escopo curto e contido; `critical` exige um
caminho de dano grave nomeado — quebrar o nucleo de auth/sessoes, escalada de
privilegio, vazamento entre tenants, perda de dados, movimentacao de dinheiro,
gateway de pagamento, criptografia/segredos, recuperacao de conta, migration
destrutiva, queda de producao ou operacao irreversivel de grande blast radius.

Tocar uma area sensivel nao escala nada por si. Feature grande, migration
controlada, permissoes, dados financeiros, muitos testes ou muitos arquivos
continuam `standard`. O script `scripts/agent-framework-route` expoe a mesma
politica de forma executavel e sem efeitos colaterais.

> O kernel completo e uma capacidade disponivel, nao o fluxo obrigatorio.

### O modo pertence a tarefa

Uma fase pode conter tarefas `fast`, `standard` e `critical` ao mesmo tempo, e
uma tarefa `critical` nao eleva as vizinhas. A resolucao e do mais especifico
para o mais geral, nunca pelo maximo:

```text
STATE.md task_modes[<id>] → execution_mode em TASKS.md
                          → default_execution_mode da fase
                          → execution_mode do projeto (default, nao piso)
                          → standard
```

Para corrigir uma classificacao ja registrada:

```bash
./scripts/framework-next set-execution-mode \
  --project /caminho/do/projeto \
  --scope task --task-id U3A --to standard \
  --reason "Frontend delimitado, sem backend, sem migration" \
  --actor "<quem>"
```

Escalar para `critical` exige `--risk` nomeando o dano grave; reduzir exige
apenas `--reason`. A operacao grava em `STATE.md` e no ledger de evidencias, e
nunca reescreve plano selado, review ou evidencia historica.

Veja `kernel/adaptive-execution-policy.md` para matriz de templates, budget de
verificacao, severidades de review e reuso de contexto, e
`workflows/execution-mode-classification.md` para o passo a passo.

### Persistencia sem cerimonia

Persistencia e cerimonia sao escolhas separadas. Um projeto que so precisa
sobreviver a outra sessao usa a inicializacao leve, que cria somente
`.agent/STATE.md` e `.agent/PLAN.md`:

```bash
./scripts/framework-next init \
  --project /caminho/do/projeto \
  --name example-project \
  --mode standard
```

Um projeto que precisa do kernel completo — fases, contratos, gates, ledger —
sem declarar tudo `critical` usa `--persistent`:

```bash
./scripts/framework-next init \
  --project /caminho/do/projeto \
  --name example-project \
  --mode standard --persistent
```

`fast` recusa inicializacao persistente. O plan seal e as duas reviews
independentes continuam exclusivos das tarefas `critical`.

## CI Throughput Policy

```text
CI gates integration, not continuous development.
```

CI bloqueia **merge**. Nao bloqueia, por si so, continuar programando. O modo de
execucao e o perfil de CI sao eixos separados:

| Eixo | Pergunta | Valores |
| --- | --- | --- |
| `execution_mode` | Quanta cerimonia um defeito aqui merece? | `fast`, `standard`, `critical` |
| `ci_profile` | Quais gates este diff deve? | `minimal`, `targeted`, `full` |

`critical` implica `full`. `standard` nao implica nada: pode rodar `minimal`
(README), `targeted` (a maior parte da implementacao) ou `full` (tem migration).

### Tres distincoes que a politica existe para preservar

```text
MERGE BLOCKER          gate que precisa estar verde antes de integrar
NEXT-WORK BLOCKER      motivo para a proxima unidade nao comecar (raro)
POST-MERGE OBSERVATION run que reporta, nao autoriza
```

### Em vez de esperar

```text
antes:  push PR → espera CI → so entao continua
agora:  push PR → classifica dependencia da proxima unidade
                → continua quando seguro
                → volta ao CI no merge boundary
```

- `continue_independent` — a proxima unidade nao depende da PR pendente: comece
  da base de integracao, em worktree propria.
- `stack_local` — depende: branch **local** a partir da HEAD pendente, sem
  publicar PR dependente antes da pai integrar; depois do merge, rebase e so
  entao valide e publique.
- `wait` — so quando o resultado do CI muda a proxima decisao, risco critico
  proibe trabalho especulativo ou dependencia externa impede continuar.

### Perfis e espera

```yaml
ci_profile:        minimal | targeted | full
ci_blocking_point: before_merge | now | none
ci_wait_policy:    background | blocking_before_merge | blocking_now
publication_hold:  true quando nada pode ser publicado sobre esta unidade
next_work_policy:  continue_independent | stack_local | wait
```

`ci_blocking_point` e `ci_wait_policy` sao eixos distintos. Perfil `full` **nao**
gera espera por si: levanta `publication_hold` e, havendo trabalho seguro,
mantem `background`. `blocking_before_merge` so aparece quando nao sobrou nada
seguro para fazer. `blocking_now` exige razao nomeada — release ou deploy ativo,
dependencia externa, resultado que muda a proxima decisao, ou risco critico que
proibe trabalho especulativo. "CI rodando", perfil `full` e modo `critical` nao
sao razoes.

O router reporta o eixo de CI junto com o modo, e recebe contexto operacional
como dado — nunca como texto ambiguo no pedido:

```bash
./scripts/agent-framework-route --auto \
  --runner-kind self_hosted_shared --remote-ci-running \
  --next-unit dependent --unit-ref pr-42 \
  "Implemente a tela de fornecedores no frontend."
```

```text
selected_mode: standard
ci_profile: targeted
ci_blocking_point: before_merge
ci_wait_policy: background
next_work_policy: stack_local
local_gates: lint, typecheck
local_verification: targeted
deferred_gates: e2e-full-regression → nightly, release ou perfil full explicito
MERGE BLOCKER: lint, typecheck, component-tests-affected pending
NEXT-WORK BLOCKER: none — stack_local permitted
POST-MERGE OBSERVATION: main CI: not_applicable
```

Tambem aceita `--ci-context-json '{...}'`. Campo ausente usa default
documentado: runner nao declarado e tratado como compartilhado, e dependencia
nao declarada **nunca** vira dependencia confirmada.

### Exemplos

| # | Situacao | Perfil | Blocking point | Wait | Proxima unidade |
| --- | --- | --- | --- | --- | --- |
| A | frontend `standard`, proxima unidade depende | `targeted` | `before_merge` | `background` | `stack_local` |
| B | docs-only | `minimal` | `before_merge` | `background` | `continue_independent` |
| C | migration `critical`, existe trabalho seguro | `full` | `before_merge` | `background` (`publication_hold`) | `continue_independent` |
| D | release ativo | `full` | `now` | `blocking_now` | `wait` |
| E | shared runner ocupado | `targeted` | `before_merge` | `background`, gates locais pesados em espera | edicao continua |

### Runner self-hosted compartilhado

Enquanto uma run remota executa na mesma maquina de desenvolvimento: leitura,
edicao, escrita de teste, planejamento, analise e review continuam liberados;
suite completa, Playwright, builds Docker/Next e E2E local ficam em espera.
Contencao de recurso **nao** e instabilidade de runner. Runner hospedado ou
self-hosted dedicado nao gera contencao — isso e capability do executor, nunca
uma exigencia do framework.

### Main CI

Se a arvore exata do merge ja foi validada pela PR e o workflow de `main` nao
adiciona gate funcional novo, a run de `main` **observa**: nao segura a proxima
unidade segura. `main` vermelho continua sendo incidente a investigar.

### Onde a politica para

Gate kind e abstrato (`unit-tests-affected`, nao `pnpm vitest run --changed`). O
binding para comandos reais do repositorio e de `test-confidence-mapper`. O
framework nao versiona configuracao de CI especifica de repo nem
`.agent/ci-profile.yml`.

Detalhes em `kernel/ci-throughput-policy.md`; sequencia operacional em
`workflows/ci-throughput.md`; referencia executavel em
`kernel/runtime/ci_policy.py`; decisao por unidade via
`/ci-throughput-controller`.

## Kernel persistente `critical` (P0 + P1)

Em `critical`, o kernel coordena os assets existentes sem substitui-los e mantém
o protocolo persistente completo:

```text
Route
→ Ground
→ Discuss
→ Specify
→ Plan
→ Execute
→ Review
→ Verify
→ Ship
→ Learn
```

As regras centrais ficam separadas em:

- `kernel/protocol.md`: ciclo, papeis, retomada, blockers e conclusao;
- `kernel/adaptive-execution-policy.md`: selecao de modo e proporcionalidade;
- `kernel/state-machine.md`: estados, transicoes e guards;
- `kernel/execution-policy.md`: escopo, concorrencia, retries e Git;
- `kernel/delegation-policy.md`: contexto limpo e retorno de subagente;
- `kernel/evidence-policy.md`: evidencia, inferencia, waiver e ledger;
- `kernel/test-policy.yaml`: politica executavel por tipo de mudanca.

O runtime usa apenas Python 3 e biblioteca padrao. `STATE.md` usa frontmatter JSON,
que tambem e YAML 1.2 valido: e legivel, deterministico e nao exige PyYAML.

### Inicializar `.agent/` explicitamente

Na raiz deste framework, rode:

```bash
./scripts/framework-next init \
  --project /caminho/do/projeto \
  --name example-project \
  --mode critical
```

A inicializacao e atomica e nunca sobrescreve uma pasta `.agent/` existente. Ela
nao ocorre durante roteamento `fast`. No caminho `critical`, cria:

```text
.agent/
├── PROJECT.md
├── ROADMAP.md
├── STATE.md
├── CONTEXT.md
├── DECISIONS.md
├── REQUIREMENTS.md
└── phases/
```

Crie os artefatos da primeira fase com:

```bash
./scripts/framework-next init-phase \
  --project /caminho/do/projeto \
  --id P1 \
  --name "Example phase" \
  --slug 01-example
```

Cada fase possui `SPEC.md`, `PLAN.md`, `TASKS.md`, `EVIDENCE.md`, `REVIEW.md` e
`HANDOFF.md`. `TASKS.md` contém os contratos completos, não apenas links ou
resumos.

### Retomar com `framework-next`

```bash
./scripts/framework-next --project /caminho/do/projeto
```

A saída contém `Current state`, `Execution mode`, `Detected evidence`, `Inconsistencies`,
`Next operation`, `Required asset` e `Blocking conditions`. O comando observa
estado, artefatos e Git e retorna exatamente uma operação. Referência ausente,
contexto stale, tarefa sem contrato ou blocker impede avanço.

Para validar o estado:

```bash
./scripts/framework-next validate --project /caminho/do/projeto
```

`validate` nunca modifica arquivos. Ele sai com `0` quando existem apenas avisos
e com `2` quando existe erro.

### Estado portátil entre computadores

`.agent/STATE.md` é estado compartilhado e versionado, então nunca guarda um
caminho que só existe em uma máquina. O campo `git.worktree` aceita `"."` — a
raiz do repositório Git que contém `.agent/` — ou `null`. A raiz absoluta é
descoberta em runtime com `git rev-parse --show-toplevel` e vive apenas em
memória. O mesmo branch pode ser usado em clones de máquinas diferentes:

```text
macOS    /Users/voce/dev/projeto
Linux    /home/voce/projeto
Windows  C:\Users\voce\dev\projeto
```

Os três validam o mesmo `STATE.md` sem edição e sem gerar diff.

Caminhos absolutos escritos por kernels antigos continuam carregando; eles são
relatados como aviso `git-worktree-legacy`, não como projeto inválido. Para
converter o campo, use a operação explícita:

```bash
./scripts/framework-next normalize-worktree --project /caminho/do/projeto
./scripts/framework-next normalize-worktree --project /caminho/do/projeto --check
```

Ela altera somente a linha `worktree`, é idempotente, nunca grava outro caminho
absoluto e recusa executar quando não puder provar qual é o repositório.

Quando o trabalho de uma fase já existe em Git mas o estado ficou preso numa
fase anterior — commits, testes e revisões feitos antes de a fase ter índice
executável —, use a reconciliação. Ela reaponta os artefatos, re-sela o plano sob
uma decisão registrada e para em `verifying`, para que o portão de shipping
continue decidindo:

```bash
./scripts/framework-next reconcile-phase \
  --project /caminho/do/projeto \
  --id E --name "Hardening" --slug E \
  --decision D-021 \
  --evidence .agent/phases/E/EVIDENCE.md#reconciliacao \
  --version 4 \
  --actor reconciliation
```

Ela recusa executar se alguma tarefa da fase não estiver `verified`, se houver
blocker aberto, se a decisão não estiver em `DECISIONS.md`, se a evidência não
existir, se a revisão do plano não aumentar, ou se houver mudança de produto não
commitada. Nenhum portão é enfraquecido: a reconciliação descreve trabalho
concluído, não o aprova.

Para aplicar uma transição já suportada por evidência persistida:

```bash
./scripts/framework-next transition \
  --project /caminho/do/projeto \
  --to executing \
  --actor workflow-runner \
  --reason "Plan gate passed and P1-T01 is eligible"
```

Depois do plan gate e antes de `specified → planned`, sele o plano:

```bash
./scripts/framework-next seal-plan \
  --project /caminho/do/projeto \
  --version 1 \
  --decision DEC-001 \
  --evidence ".agent/phases/01-example/EVIDENCE.md#plan-gate" \
  --actor workflow-planner
```

Mudança posterior em `PLAN.md` ou `TASKS.md` invalida o fingerprint e bloqueia
execução até revisão explícita e novo seal.

Quando a revisão explícita acontece **com a tarefa já em andamento** — o caso de
uma CI que reprova e prova que o contrato, não o código, estava errado —
`seal-plan` não serve: ele só aceita `specified`. Use a emenda:

```bash
./scripts/framework-next amend-plan \
  --project /caminho/do/projeto \
  --decision D-047 \
  --evidence ".agent/phases/01-example/EVIDENCE.md#event-2026-08-02T17:09:38+00:00" \
  --actor planner \
  --reason "CI expôs contrato defeituoso da tarefa ativa"
```

Ela vale de `executing`, `reviewing` ou `verifying`, com `current_task` não
integrada, plano já selado e artefatos realmente alterados. A revisão avança em
um, **o fingerprint é calculado pelo kernel** (não existe argumento para
informá-lo; `--version` é confirmação, não escolha), os cinco gates de revisão
reabrem, fase e tarefa voltam a `executing` e o binding de execução atravessa
byte a byte — sem liberar e recapturar, porque o trabalho não recomeçou.

Aprovações antigas viram histórico carimbado com a revisão em que foram dadas;
nada é apagado. Nenhum blocker é exigido ou inventado: decisão e evidência já
explicam a emenda. **Nunca** edite o fingerprint à mão, e **nunca** use uma spec
review `BLOCKED` como mecanismo de replanejamento — ver
`workflows/ci-contract-correction.md`.

`ready_to_ship → shipped` lê `gates.release`. O gate só chega a `passed` com
decisão registrada em `DECISIONS.md` e evidência que resolva para um arquivo
real da fase ativa:

```bash
./scripts/framework-next gate-status \
  --project /caminho/do/projeto \
  --gate release --to passed \
  --decision D-043 \
  --evidence ".agent/phases/01-example/EVIDENCE.md#release" \
  --actor releaser \
  --note "PR #25 mergeado, CI verde"
```

O comando registra a mudança no ledger da fase e **não** executa a transição:
passar o gate e dar `shipped` continuam dois atos deliberados. `spec_compliance`
e `code_quality` são recusados aqui — pertencem a `validate-spec-review` e
`validate-quality-review`, que validam o próprio documento de revisão. Repetir a
mesma mudança é no-op; repetir com outra justificativa é recusado.

### Reclassificação formal do modo

`set-execution-mode` é o único escritor de classificação. Ele grava o modo, o
valor anterior, o motivo e — em escaladas — o caminho de dano grave nomeado, em
`STATE.md`, e anexa um evento `classification` ao ledger da fase:

```bash
./scripts/framework-next set-execution-mode \
  --project /caminho/do/projeto \
  --scope task --task-id U3B1 --to critical \
  --risk cross_tenant_exposure \
  --reason "A consulta nova atravessa o filtro de tenant" \
  --actor planner
```

O registro fica em `STATE.md`, nunca em `TASKS.md`: uma classificação não faz
parte do contrato que o selo congelou, e reescrever o índice selado para
corrigir um rótulo exigiria quebrar o fingerprint ou re-selar tudo. `--check`
não escreve nada, repetir uma classificação vigente é no-op, e a classificação
anterior vai para `history`. `--scope project` altera o default do projeto sem
perder o kernel persistente.

### Aplicação formal de revisões

Cada gate de revisão tem **um único escritor**, e ele valida e aplica na mesma
operação:

| Gate | Escritor formal | Recusado por |
| --- | --- | --- |
| `spec_compliance` | `validate-spec-review` | `gate-status` |
| `code_quality` | `validate-quality-review` | `gate-status` |

```bash
./scripts/framework-next validate-spec-review \
  --project /caminho/do/projeto \
  --contract .agent/phases/01-example/TASKS.md --task-id U3A \
  --result .agent/phases/01-example/U3A-result.md \
  --review .agent/phases/01-example/U3A-spec-review.md \
  --actor reviewer-cli
```

Validar e aplicar são **um ato só**. Um estado durável em que a revisão foi
validada mas não registrada é a mesma meia-verdade que o framework recusa em
todo lugar: o veredito existe e nada no estado persistido pode ser perguntado
sobre ele. Use `--check` para rodar todos os guards **sem escrever nada**.

Classificações mapeiam para os estados reais dos gates, sem inventar
vocabulário: `PASS → passed`, `PASS_WITH_NOTES → passed_with_notes`,
`BLOCKED → blocked`; `APPROVED → approved`, `APPROVED_WITH_NOTES →
approved_with_notes`, `CHANGES_REQUIRED → changes_required`. Não existe
`REJECTED`.

A aplicação **não** move o ciclo de vida. Uma aprovação de spec deixa fase e
tarefa em `reviewing` e aponta para `run-quality-review`. Uma aprovação de
qualidade move a tarefa para `reviewed` — sem isso `reviewing → verifying` seria
recusada no índice, porque não existe aresta `reviewing → verifying` em
`TASK_STATUS_TRANSITIONS` — e aponta para `verify-phase`. A transição continua
sendo um ato deliberado, com actor e razão próprios.

Um veredito bloqueante registra o gate, abre os blockers com evidência e aponta
`return-to-execution`; ele também não executa a transição. Depois da correção,
`transition --to executing` reabre os cinco gates de revisão — nenhuma aprovação
é herdada.

**Abaixo de `critical`, a correção fecha a rodada que ela responde.** Rode os
testes afetados pela correção, registre cada achado como resolvido com essa
evidência (`framework-next resolve-finding --blocker <ID> --evidence <arquivo>
--actor <quem>`) e vá direto para verificação:

```text
reviewing → executing → correção → findings resolved → verifying
```

Nada é apagado: o achado guarda `resolution`, `resolution_evidence` e quem
registrou, e a review bloqueante permanece em `gate_records[...].history`. Uma
segunda review só volta a ser exigida quando a correção expandiu materialmente o
escopo, revelou risco grave ou mudou o contrato — isso é `amend-plan`, que
reabre os gates e devolve a tarefa a `reviewing`, agrupando numa única emenda o
que foi mecanicamente afetado (arquivos gerados, migration head, mapas
arquiteturais). Em `critical` `resolve-finding` é recusado e **as duas revisões
são pagas de novo**. Uma correção de código que não altera o contrato **não** é
caso de `amend-plan`.

Toda aplicação exige independência (reviewer ≠ executor), diff inspecionado,
`files_inspected` e `evidence_inspected` não vazios, e correspondência com o
trabalho real: task, fase, `plan_revision`, commit revisado e branch vinculada.
Uma revisão é **carimbada com a revisão do plano** sob a qual foi concedida:
depois de `amend-plan` a aprovação antiga vira histórico e uma revisão da v1 é
recusada contra a v2. Repetir a mesma aplicação é no-op; repetir com outro
relatório, resultado, reviewer, SHA ou revisão é recusado — inclusive quando o
relatório foi editado depois de aplicado, porque o digest do documento faz parte
da identidade.

Quatro documentos se movem juntos — ledger, `REVIEW.md`, `TASKS.md` e
`STATE.md` — nessa ordem, com rollback byte a byte se qualquer etapa falhar.
Ver `workflows/review-application.md`.

`shipped` significa fase integrada e encerrada no ciclo controlado de
desenvolvimento, **não** liberação em produção. Blockers externos de produção
continuam registrados e abertos sem reabrir a fase concluída.

Quando a próxima fase já está contratada em disco — SPEC, PLAN e TASKS escritos
enquanto a fase anterior ainda rodava — nenhuma operação ordinária a alcança:
`init-phase` recusa diretório existente, `seal-plan` só sela a fase ativa e
`reconcile-phase` exige trabalho concluído. Use a rotação:

```bash
./scripts/framework-next activate-phase \
  --project /caminho/do/projeto \
  --id U3 --name "Onboarding e setup" \
  --slug u3-membership-onboarding \
  --actor planner \
  --reason "U2 encerrada; U3 já contratada"
```

Ela exige a fase atual em `shipped` ou `superseded`, a fase de destino presente
no roadmap com os seis artefatos, nenhuma tarefa executada e grafo de tarefas
válido. A fase anterior é preservada e registrada em `completed_phases`.

O plano só conta como selado quando o fingerprint armazenado, recalculado contra
a fase ativada, ainda confere; caso contrário o estado aterrissa em `specified`
e o gate de plano é pago de novo. Ativar uma fase **nunca** produz `execute-task`
prematuro. Ver `workflows/phase-rotation.md`.

`execute-task -> <id>` é operação executável, não apenas recomendação:

```bash
./scripts/framework-next start-task \
  --project /caminho/do/projeto \
  --actor workflow-runner \
  --reason "Plan gate passed and U3A is eligible"
```

Ela seleciona a tarefa elegível, move tarefa e fase para `executing`, captura o
binding de branch e registra o evento — **numa operação só**. O alvo vem do
kernel: `--task-id` é aceito apenas como confirmação e recusa se divergir. Não
existe `select-task`, e `current_task.id` não tem outro escritor prospectivo.

`task-status` não seleciona tarefa; `transition` não inventa `current_task`;
`reconcile-phase` é retrospectiva e não serve para iniciar trabalho. Nenhum
hand-edit de `STATE.md` é necessário. Os três documentos — `TASKS.md`,
`STATE.md` e o ledger — se movem juntos, com rollback se qualquer etapa falhar.

A afinidade de branch começa com a **execução**, não com o planejamento.
`executing`, `reviewing` e `verifying` exigem que o checkout seja a branch
vinculada; todos os demais estados — incluindo `planned` — não têm afinidade.
Um plano selado é um plano aprovado, não um plano em execução, e a branch de
implementação pode ainda não existir.

O vínculo nasce ao iniciar a tarefa: `transition --to executing` lê a branch do
Git e grava `current_task.execution`. Ele é **capturado, nunca declarado** —
nenhum comando aceita argumento de branch, então o vínculo não pode nomear uma
branch que não está em uso. Iniciar é recusado em `HEAD` destacado e na própria
`base_branch`.

Sair da execução libera o vínculo para `git.last_execution`, que é histórico e
nunca é validado. Assim os dois sentidos param de disputar o mesmo campo: a
branch onde o trabalho **deve** estar, e a branch onde ele **esteve**. Uma branch
mergeada pode ser apagada e a branch de integração continua válida, sem
hand-edit. Ver `workflows/task-start.md`.

Se o checkout sair da branch vinculada durante a execução, a próxima operação é
`restore-execution-branch` — a correção é um `git switch`, não uma edição de
`STATE.md`. `validate` nunca escreve, em nenhum estado.

Os estados formais são:

```text
proposed
discussing
specified
planned
executing
reviewing
verifying
ready_to_ship
shipped
blocked
cancelled
superseded
```

Consulte `kernel/state-machine.md` para a tabela completa. Em especial,
`planned → executing` exige plano aprovado, risco classificado, contrato integral
e dependências satisfeitas; `verifying → ready_to_ship` exige aceite, checks,
blockers e waivers válidos.

### Planejamento e execução `critical`

- `workflow-planner` escolhe workflow, risco, dependências, skills, gates,
  paralelismo e contratos. Ele termina em `planned` e não implementa.
- `workflow-runner` consome `STATE.md`, escolhe uma tarefa elegível, monta contexto,
  aciona executor/reviewers/verifier e controla transições.
- `workflow-orchestrator` continua disponível como alias de compatibilidade e
  encaminha para os dois papeis separados.

Uma tarefa é executada por `task-runner` com o contrato integral. O validador
aplica `kernel/test-policy.yaml`, limita os arquivos, exige evidência por critério
e aceita no máximo o resultado `implementation_complete`:

```bash
./scripts/framework-next validate-task \
  --project /caminho/do/projeto \
  --contract .agent/phases/01-example/TASKS.md \
  --task-id P1-T01

./scripts/framework-next validate-result \
  --project /caminho/do/projeto \
  --contract .agent/phases/01-example/TASKS.md \
  --task-id P1-T01 \
  --result /caminho/task-result.md
```

Regras de negócio usam RED → GREEN → refactor; bugfix começa pela regressão;
legado usa caracterização; API, migration, integração, UI e configuração possuem
gates próprios. Waiver precisa motivo específico, aprovação e evidência
alternativa.

### Reviews e evidências `critical`

O executor faz self-review, mas não aprova o próprio trabalho. Os reviews
independentes são ordenados:

1. `spec-compliance-reviewer`: critérios, requisitos, decisões, escopo e waivers;
2. `code-quality-reviewer`: bugs, padrões, segurança, performance, erros, testes,
   manutenção e compatibilidade.

`BLOCKED` ou `CHANGES_REQUIRED` retorna a tarefa a `executing`, preserva a falha
em `EVIDENCE.md` e invalida aprovações afetadas. Depois de correcao localizada,
repita somente o review, criterios e regressoes afetados.

O ledger aceita comandos/testes, diff, screenshots, queries, APIs, logs, reviews,
validação manual, waivers, blockers, correções e commits. Uma afirmação do
implementador não conta como evidência por si só.

### Fluxos de feature e bugfix por modo

Feature:

```text
fast: inspect → implement → targeted tests → diff review
standard: focused grounding → short plan → implement → tests → integrated review
critical: full persistent lifecycle
```

Bugfix:

```text
fast: reproduce → fix → targeted regression test → review
standard: investigate → short plan → regression test → fix → integrated review
critical: persistent debug → evidence → contracts → split reviews
```

Investigações bloqueadas usam `workflows/blocked-investigation.md` e
`persistent-debug-session`; retomam somente o estado salvo em `blocked_from`.

### Exemplo mínimo completo

Uma solicitação “normalizar tipos externos sem perder valores desconhecidos”
vira:

```text
REQ-004/REQ-007 em REQUIREMENTS.md
→ AC-01..AC-03 em SPEC.md
→ P1-T03 no grafo de PLAN.md
→ contrato integral em TASKS.md
→ task-runner registra RED/GREEN/refactor e implementation_complete
→ spec reviewer prova cada AC
→ quality reviewer aprova o diff
→ EVIDENCE.md associa testes/codigo/reviews a cada AC
→ runner registra commit atomico e tarefa verified
→ framework-next seleciona a proxima tarefa elegivel
```

Em outra sessão de um fluxo persistente, rode `framework-next`.
`context-compressor` gera um handoff complementar, mas `STATE.md` continua sendo
a fonte do lifecycle.

### Compatibilidade e migração

Skills e workflows antigos continuam com os mesmos nomes. `workflow-orchestrator`
é um alias documentado; novos consumidores devem usar `workflow-planner` e
`workflow-runner`. Projetos sem `.agent/` continuam utilizáveis e só são
inicializados por comando explícito. Estados P0/P1 sem `execution_mode` sao
interpretados como `critical`; novas inicializacoes registram o campo. Aliases
legados `quick`, `full` e `audit` continuam aceitos como `standard`, `critical`
e `critical`.

A calibracao por tarefa e opt-in: um projeto `critical` sem `execution_mode` em
nenhuma tarefa continua com o lifecycle integral, incluindo plan seal e duas
reviews independentes. A cerimonia so diminui quando alguem classifica a tarefa
explicitamente — no contrato, no default da fase, ou por
`framework-next set-execution-mode`.

Os installers agora sincronizam, arquivo a arquivo, skills e assets compartilhados
(`kernel`, workflows, rubrics, templates, docs, scripts e installers), preservando
arquivos externos e criando backup antes de substituir nomes existentes. Veja
`docs/kernel-migration.md`.

## Instalar no Codex

```bash
bash ~/agent-framework/installers/install-codex.sh
```

Use skills com `$skill-name`:

```text
$project-context-loader Prepare contexto do repo.
$diff-reviewer Revise o diff atual.
```

## Instalar no Claude Code

```bash
bash ~/agent-framework/installers/install-claude.sh
```

Use skills com `/skill-name`:

```text
/repo-map-builder Mapeie entrypoints e rotas.
/bug-repro-lab Investigue este stack trace.
```

## Instalar em todos

```bash
bash ~/agent-framework/installers/install-all.sh
```

Os installers copiam diretorios em `skills/` que possuem `SKILL.md` e sincronizam
os assets compartilhados necessários às referências relativas. Skills e arquivos
externos que não existem no framework não são removidos. Itens de mesmo nome são
salvos em backup oculto antes da substituição.

## Verificar

```bash
bash ~/agent-framework/installers/verify-framework.sh
```

Testes do kernel:

```bash
python3 -m unittest discover -s tests -v
```

## Checagem de seguranca

```bash
make security:check
```

Ou:

```bash
./scripts/security-check
```

## Atualizar em outro computador

```bash
cd ~/agent-framework
git pull --ff-only
bash installers/verify-framework.sh
bash installers/install-all.sh
```

Ou use:

```bash
bash ~/agent-framework/installers/update-framework.sh
bash ~/agent-framework/installers/install-all.sh
```

## Adicionar nova skill

```text
skills/nova-skill/
  SKILL.md
```

O `SKILL.md` deve ter frontmatter:

```yaml
---
name: nova-skill
description: Use para ...
---
```

Mantenha a skill curta. Conteudo longo deve ir para `rubrics/`, `workflows/`, `templates/` ou `docs/`.

Use `docs/skill-standards.md` como padrao de criacao e rode:

```bash
bash installers/verify-framework.sh
```

## Evolucao continua

Use `$skill-evolution-loop` para registrar tarefas recorrentes em `docs/task-memory.md`. Quando o mesmo padrao aparecer 3 vezes em tarefas distintas, a skill decide se deve criar uma nova skill, atualizar uma existente ou extrair uma rubric/template.

Use `docs/framework-roadmap.md` para backlog de melhorias e proximas skills candidatas.

Use `docs/agent-workflow-roadmap.md` para evoluir skills e workflows de criacao, refatoracao, guardrails, tools, QA e review obrigatorio de agentes.

Nucleo inicial para agentes:

```text
$agent-builder Planeje ou refatore um agente com tools, memoria, guardrails e validacao.
```

Etapa anti-hardcode para agentes:

```text
$agent-anti-hardcode-auditor Audite modelo, prompt, tools, paths e env vars hardcoded.
$model-flexibility-auditor Verifique fallback e troca segura de modelo/provider.
$config-surface-auditor Revise env vars, defaults, .env.example e .gitignore.
```

Refinamento de prompt por acao:

```text
$prompt-refiner Refine este pedido no modo implementation/debug/review/research/runtime-qa.
$agent-prompt-refiner Refine este system prompt com tools, guardrails e evals.
```

Tools para agentes:

```text
$agent-tool-designer Desenhe uma tool com schema, permissao, side effects e erros.
$tool-contract-auditor Audite contrato, timeout, retry, idempotencia e logs da tool.
$tool-runtime-validator Valide a tool em execucao com casos reais e falhas.
```

Guardrails e seguranca para agentes:

```text
$agent-guardrails-implementer Especifique guardrails de input, output, tools e logs.
$agent-security-auditor Audite prompt injection, vazamento, tools inseguras e permissoes.
$env-gitignore-auditor Revise .gitignore, .env.example, tokens, logs e artefatos.
```

Runtime QA, evals e observabilidade para agentes:

```text
$agent-eval-planner Planeje evals simples para prompt, tools, fallback e regressao.
$agent-observability-auditor Audite logs, traces, custo, redaction e debug readiness.
$agent-runtime-qa Valide o agente rodando com falhas, fallback e escalacao.
```

Logging proporcional para features:

```text
$feature-logging-planner Avalie se esta feature precisa de logs e onde logar sem ruido.
```

Code review obrigatorio:

```text
$code-review-gate Decida se este diff precisa review simples, profundo ou cross-area.
$agent-code-reviewer Revise prompt, tools, guardrails, config, logs, fallback e testes.
```

Git, commit e PR:

```text
$git-decision-router Decida commit direto, esperar validacao, branch, PR ou unstaged.
$commit-readiness-checker Cheque escopo, testes, secrets e mensagem antes do commit.
$pr-description-builder Gere descricao de PR com evidencias, riscos e rollback.
```

Documentacao e ADR:

```text
$documentation-decision-router Decida ADR, README, runbook, agent docs, changelog ou nada.
$agent-doc-writer Documente agente com tools, env, guardrails, evals e troubleshooting.
```

Deadcode e otimizacao:

```text
$deadcode-orphan-mapper Mapeie codigo morto, prompts/tools orfaos e configs antigas.
$agent-optimization-auditor Audite tokens, latencia, tool calls, cache e model tier.
$performance-budget-auditor Audite latencia, custo, queries, memoria, batch e timeout.
```

## GSD-lite para backend

Use `$task-mode-router` antes de tarefas de backend quando quiser escolher entre
`fast`, `standard` ou `critical`. Backend simples nao e automaticamente
`critical`, e nem migration controlada, entidade nova, endpoint novo ou
autorizacao seguindo padroes ja estabelecidos: tudo isso e `standard`.

Fluxo completo quando o risco justificar:

```text
$task-mode-router Classifique a tarefa.
$backend-slice-planner Planeje fatias backend verificaveis.
$plan-quality-checker Audite o plano antes de executar.
$goal-coverage-verifier Verifique objetivo, contratos e testes apos implementar.
```

Skills complementares para backend:

```text
$test-confidence-mapper Mapeie comandos por nivel de confianca.
$dependency-risk-auditor Audite nova dependencia antes de instalar.
$persistent-debug-session Mantenha investigacao longa de bug com estado persistente.
```

Fechamento de entrega backend:

```text
$data-migration-auditor Audite schema, backfill e rollback.
$docs-sync-auditor Confira README, env vars, API docs e release notes.
$backend-release-packager Monte pacote final com evidencias, riscos e rollback.
```

## GitHub privado

```bash
cd ~/agent-framework
git init
git add .
git commit -m "Initial agent framework"
git branch -M main
git remote add origin git@github.com:SEU_USUARIO/agent-framework.git
git push -u origin main
```

Nao inclua secrets. Revise `.gitignore` antes do primeiro commit.

## Exemplos combinando skills

Bugfix:

```text
$project-context-loader Prepare contexto.
$bug-repro-lab Reproduza o bug.
$test-strategy-builder Defina regressao.
$diff-reviewer Revise o patch.
```

Refatoracao de API:

```text
$repo-map-builder Localize rotas e contratos.
$api-contract-auditor Avalie compatibilidade.
$implementation-planner Divida em fases.
$release-verifier Verifique readiness.
```

Handoff:

```text
$context-compressor Gere resumo de retomada.
$handoff-builder Monte handoff para Claude Code.
```
