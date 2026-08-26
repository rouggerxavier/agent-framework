# CI Throughput Decision — <unidade/PR>

> CI bloqueia **integracao**, nao producao de codigo.
> "nao pode mergear" e "nao pode continuar trabalhando" sao afirmacoes
> diferentes. A primeira e o normal; a segunda exige razao nomeada.
> Preencha os tres blocos de bloqueio separadamente: eles respondem perguntas
> diferentes e nunca devem ser lidos como o mesmo.

## Contexto
- Mudanca:
- Modo de execucao: fast | standard | critical
- Impactos: docs | metadata | mechanical_refactor | frontend | backend | contracts | database | security_core | e2e_relevant | release
- Runner: hosted | self_hosted_dedicated | self_hosted_shared | unknown
- Run remoto em execucao: sim | nao
- Proxima unidade: independente | dependente | nenhuma | nao declarada

Campos nao declarados usam os defaults documentados em
`kernel/ci-throughput-policy.md`. Nao invente contexto: dependencia nao declarada
nao e dependencia confirmada.

## Decisao
```yaml
selected_mode:
ci_profile:            # minimal | targeted | full
ci_blocking_point:     # before_merge | now | none
ci_wait_policy:        # background | blocking_before_merge | blocking_now
publication_hold:      # true quando nada pode ser publicado sobre esta unidade
next_work_policy:      # continue_independent | stack_local | wait
e2e_tier:              # none | focal | operational | full_regression
```

`ci_profile: full` **nao** implica `blocking_now`. Implica `publication_hold` e
`ci_blocking_point: before_merge`. `blocking_now` exige uma razao nomeada abaixo.

## Bloqueios

### 1. MERGE BLOCKER — impede **integrar**
- Gates pendentes:
- Consequencia: a PR nao entra ate ficar verde.
- Nao impede: escrever codigo, revisar, planejar, commitar em branch local.

### 2. NEXT-WORK BLOCKER — impede **continuar trabalhando**
- Razao nomeada (ou `none`):
  - [ ] resultado do CI muda a proxima decisao
  - [ ] release em andamento
  - [ ] deploy em andamento
  - [ ] dependencia externa impede continuar
  - [ ] risco critico proibe trabalho especulativo
- Se nenhuma marcada: **`none`** — o teclado esta livre.
- "CI ainda esta rodando" **nao** e uma razao. Nem perfil `full`, nem modo
  `critical`.

### 3. POST-MERGE OBSERVATION — apenas **reporta**
- Papel da run de `main`: gate | observation | incident | not_applicable
- Arvore exata do merge ja validada pela PR: sim | nao
- Workflow de `main` adiciona gate novo: sim | nao
- `main` vermelho e incidente a investigar, sempre.

Formato de saida:
```text
MERGE BLOCKER: <gates> pending
NEXT-WORK BLOCKER: none — <policy> permitted
POST-MERGE OBSERVATION: main CI: <role>
```

## Gates
- `local_gates`:
- `remote_gates`:
- `deferred_gates`: (gate → onde roda de fato: nightly, release, perfil full)
- `local_gates_on_hold`: (segurados por contencao de runner)
- Verificacao local planejada (`local_verification`): targeted | proportional | full-suite

Gate kind e abstrato. O binding para comandos reais do repo e de
`test-confidence-mapper`.

## Runner policy
- Contencao: sim | nao
- Liberado localmente sempre: leitura, edicao, escrita de teste, planejamento,
  analise, review, documentacao.
- Em espera: suite completa, Playwright/Cypress, Docker, Next/Vite, E2E local.
- Nota: contencao de recurso **nao** e instabilidade de runner.

## Proxima unidade
- Base da branch: integration-base | pending-head
- Publicar PR dependente: sim | nao (nao, salvo workflow explicitamente stacked)
- Rebase apos merge da pai: sim | nao
- Worktree:

## Concurrency
- Grupo:
- `cancel-in-progress`: sim | nao
- Run superada nao e gate.

## Auditoria apos verde
- Escopo: incremental | full
- Alvos:

## Justificativa
