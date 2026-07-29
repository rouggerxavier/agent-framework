# Agent Framework v2 — P0/P1 Implementation Report

## 1. Diagnostico inicial

### Arquitetura encontrada

- Framework Markdown-first com 60+ skills, workflows, rubrics, templates, docs e
  installers shell.
- Nao havia runtime de estado, CLI de retomada, `.agent/`, maquina de estados ou
  suite automatizada.
- `workflow-orchestrator` misturava selecao, planejamento e recomendacao de
  execucao; os workflows executavam etapas por convencao, sem guards persistentes.
- `verify-framework.sh` validava forma das skills; `security-check` validava
  secrets e chamava o verifier.
- O working tree original continha alterações preexistentes do Cursor. Elas foram
  excluídas desta branch limpa e não fazem parte da implementação P0/P1.

### Assets reutilizados

Foram integrados diretamente: `agent-framework-router`,
`project-context-loader`, `execution-plan-builder`, `plan-quality-checker`,
`test-strategy-builder`, `goal-coverage-verifier`, `code-review-gate`,
`context-compressor`, `persistent-debug-session`, `commit-readiness-checker`,
`git-decision-router`, `pr-description-builder`, `diff-reviewer`,
`runtime-qa-audit`, `release-verifier` e planners/auditors especializados.

### Conflitos e decisoes

- Estado: frontmatter JSON, que e YAML 1.2 valido, para parsing deterministico
  com Python stdlib 3.9 e sem nova dependencia.
- Compatibilidade: `workflow-orchestrator` virou alias documentado;
  `workflow-planner` e `workflow-runner` sao os papeis novos.
- Distribuicao: installers sincronizam arquivos compartilhados individualmente,
  com backup e sem remover assets externos.
- Integridade: `PLAN.md` e o contrato imutavel de `TASKS.md` recebem SHA-256;
  `task.status` fica fora do fingerprint por ser estado mutavel.
- Isolamento: alto risco e working tree materialmente sujo bloqueiam execucao sem
  worktree registrado.
- Escopo: nenhuma implementacao de registry/packs/P2/P3.

## 2. Plano executado

| Etapa | Dependencia | Saida | Gate |
| --- | --- | --- | --- |
| Grounding | README/estrutura/skills obrigatorias | diagnostico e convencoes | leituras concluidas |
| P0 runtime | grounding | documentos, estado, transicoes, init/next | 17 testes P0 |
| P0 assets | runtime | templates, planner/runner, alias | verifier |
| P1 runtime | P0 verde | contratos, testes, waivers, reviews, ledger | 13 testes P1 |
| Integracao | P1 | workflows e skills existentes | compatibilidade |
| Docs/installers | contratos estabilizados | README, migracao, shared sync | docs audit |
| Review/verify | diff completo | correcoes e evidence final | 41 testes + security |

Riscos tratados: estado stale, referencia ausente/fora da raiz, plan drift,
scope expansion, conflito paralelo, autoaprovacao, teste alegado sem resultado,
waiver vago, review fora de ordem, blocker aberto, Git/branch/worktree
inconsistente e instalacao parcial.

## 3. Mudancas realizadas — arquivo por arquivo

### Kernel e CLI

| Arquivo | Responsabilidade e motivo | Impacto | Compatibilidade |
| --- | --- | --- | --- |
| `kernel/__init__.py` | Declara o pacote do kernel. | Permite runtime importavel. | Python 3.9 stdlib. |
| `kernel/protocol.md` | Define ciclo, papeis, persistencia, retomada e done. | Fonte central do protocolo. | Coordena assets existentes. |
| `kernel/state-machine.md` | Formaliza estados, transicoes, guards e falhas. | Lifecycle auditavel. | Mantem nomes solicitados. |
| `kernel/execution-policy.md` | Define escopo, concorrencia, retry, Git e plan seal. | Bloqueia execucao insegura. | Reusa skills Git/testes. |
| `kernel/delegation-policy.md` | Define contexto limpo, controle unico e retorno. | Evita perda de requisito/orquestrador duplo. | Nao obriga subagente. |
| `kernel/evidence-policy.md` | Define vocabulario, evidencias e ledger. | Separa claim de prova. | Alinha templates/review atuais. |
| `kernel/test-policy.yaml` | Mapeia tipo de mudanca para politica executavel. | Test runner valida RED/GREEN e gates. | JSON e YAML 1.2 valido. |
| `kernel/runtime/__init__.py` | Exporta API publica minima. | Facilita testes/consumo. | Sem dependencia externa. |
| `kernel/runtime/documents.py` | Frontmatter atomico, paths seguros, Git snapshot. | Base de persistencia/grounding. | Markdown continua humano. |
| `kernel/runtime/project.py` | Inicializacao atomica de projeto/fase. | Cria `.agent/` sem overwrite. | Projeto sem `.agent/` continua opt-in. |
| `kernel/runtime/state_machine.py` | Valida estado/transicoes, seal, Git e blockers. | Enforce dos guards P0/P1. | Alias/workflows chamam a mesma API. |
| `kernel/runtime/contracts.py` | Valida contratos, resultados, testes e task status. | Escopo/testes deixam de ser prosa. | Campos antigos podem existir fora do kernel. |
| `kernel/runtime/reviews.py` | Valida/aplica spec e quality review separados. | Impede auto-review e ordem invalida. | Reusa diff/auditors existentes. |
| `kernel/runtime/evidence.py` | Acrescenta eventos estruturados ao ledger. | Historico append-only com falhas. | Markdown com blocos JSON. |
| `kernel/runtime/next_operation.py` | Detecta uma proxima operacao por evidencia. | Retomada entre sessoes/agentes. | Nunca inventa artefato. |
| `kernel/runtime/cli.py` | Comandos init, next, seal, transition e validadores. | Operacao central executavel. | Instalavel em cada tool root. |
| `scripts/framework-next` | Wrapper shell portavel da CLI. | UX simples e `PYTHONPATH` correto. | Funciona na fonte e instalado. |

### Skills

| Arquivo | Responsabilidade e motivo | Impacto | Compatibilidade |
| --- | --- | --- | --- |
| `skills/framework-next/SKILL.md` | Entrada de init/retomada. | Uma operacao objetiva. | Nova, sem substituir router. |
| `skills/workflow-planner/SKILL.md` | Planeja ate `planned`, sem implementar. | Separa planejamento. | Reusa planners/gates atuais. |
| `skills/workflow-runner/SKILL.md` | Controla tarefas, reviews e transicoes. | Uma linha de controle. | Consome workflows atuais. |
| `skills/task-runner/SKILL.md` | Executa contrato integral e self-review. | Executor nao autoaprova. | Reusa test strategy. |
| `skills/spec-compliance-reviewer/SKILL.md` | Review de aceite/spec/escopo. | Primeira etapa independente. | Nova responsabilidade explicita. |
| `skills/code-quality-reviewer/SKILL.md` | Review tecnico apos spec. | Segunda etapa independente. | Encapsula `diff-reviewer`/auditors. |
| `skills/workflow-orchestrator/SKILL.md` | Alias para planner/runner. | Remove mistura conceitual. | Nome historico preservado. |
| `skills/agent-framework-router/SKILL.md` | Roteia retomada e novos papeis. | Kernel vira entrada quando ha estado. | Rotas antigas mantidas. |
| `skills/execution-plan-builder/SKILL.md` | Gera entradas para contratos. | Planos delegaveis viram executaveis. | Saida antiga preservada. |
| `skills/plan-quality-checker/SKILL.md` | Gate formal de `planned`. | Bloqueia contrato/grafo/risco incompleto. | Template existente ampliado. |
| `skills/project-context-loader/SKILL.md` | Grounding com commit/fatos/unknowns/staleness. | Contexto verificavel. | Saida anterior e subconjunto. |
| `skills/context-compressor/SKILL.md` | Handoff baseado em `STATE.md`. | Retomada nao depende da conversa. | Handoff antigo continua legivel. |
| `skills/persistent-debug-session/SKILL.md` | Integra blocker e `blocked_from`. | Debug sobrevive a pausa. | Template atual ampliado. |
| `skills/test-strategy-builder/SKILL.md` | Produz politica consumivel pelo runtime. | Recomendacao vira gate. | Rubric existente reutilizada. |
| `skills/goal-coverage-verifier/SKILL.md` | Autoridade de `ready_to_ship`. | Fecha aceite, checks e waivers. | Relatorio existente ampliado. |
| `skills/code-review-gate/SKILL.md` | Roteia spec e quality em ordem. | Review proporcional e separado. | Reviewers especializados preservados. |
| `skills/commit-readiness-checker/SKILL.md` | Gate de commit atomico por tarefa. | Bloqueia commit sem reviews/evidence. | Decisao Git antiga mantida. |
| `skills/git-decision-router/SKILL.md` | Worktree/branch/commit/PR proporcional. | Isolamento registrado em estado. | Sem automacao Git destrutiva. |
| `skills/pr-description-builder/SKILL.md` | PR a partir do ledger/task commits. | Evidencia honesta e rastreavel. | Template anterior ampliado. |

### Templates

| Arquivo | Responsabilidade e motivo | Impacto | Compatibilidade |
| --- | --- | --- | --- |
| `templates/project.md` | Objetivo e limites do projeto. | Gera `PROJECT.md`. | Novo. |
| `templates/project-state.md` | Schema completo de `STATE.md`. | Estado compacto/deterministico. | Schema versionado 1. |
| `templates/project-context.md` | Metadados e grounding. | Gera `CONTEXT.md`. | Campos antigos nao exigidos fora do kernel. |
| `templates/project-roadmap.md` | Milestones/dependencias. | Gera `ROADMAP.md`. | Novo. |
| `templates/project-decisions.md` | Decisoes versionadas. | Suporta plan revision. | Novo. |
| `templates/project-requirements.md` | Requisitos/links de aceite. | Gera `REQUIREMENTS.md`. | Novo. |
| `templates/phase-spec.md` | Escopo, requisitos e ACs. | Gera `SPEC.md`. | Novo. |
| `templates/phase-plan.md` | Grafo, gates, seal e rollback. | Gera `PLAN.md`. | Novo. |
| `templates/phase-tasks.md` | Indice de contratos integrais. | Gera `TASKS.md`. | JSON/YAML deterministico. |
| `templates/task-contract.md` | Contrato minimo completo. | Limita executor. | Campos adicionais opcionais fora do kernel. |
| `templates/task-result.md` | Resultado/self-review/test trace. | Validador consome diretamente. | Novo. |
| `templates/evidence-ledger.md` | Ledger por tarefa/AC/review. | Gera `EVIDENCE.md`. | Markdown auditavel. |
| `templates/evidence-event.md` | Evento append-only. | Alimenta CLI de evidence. | Novo. |
| `templates/spec-compliance-review.md` | Relatorio do review 1. | Status por AC. | Novo. |
| `templates/code-quality-review.md` | Relatorio do review 2. | Areas/findings estruturados. | Novo. |
| `templates/phase-review.md` | Historico/review da fase. | Gera `REVIEW.md`. | Novo. |
| `templates/phase-handoff.md` | Retomada da fase. | Gera `HANDOFF.md`. | Novo. |
| `templates/test-plan.md` | Change type, stages e waiver. | Politica de teste executavel. | Estrutura anterior preservada/ampliada. |
| `templates/plan-quality-report.md` | Gates de estado/contrato/grafo. | Evidencia do plan gate. | Campos antigos preservados. |
| `templates/code-review-gate-report.md` | Dois reviewers e independencia. | Review routing explicito. | Campos antigos preservados. |
| `templates/goal-coverage-report.md` | Guards/transition do verifier. | Decisao operacional. | Campos antigos preservados. |
| `templates/debug-session.md` | Blocker e condicao de retorno. | Debug persistente. | Campos antigos preservados. |
| `templates/handoff-summary.md` | Estado/tarefa/evidence/next action. | Handoff complementa state. | Campos antigos preservados. |
| `templates/commit-readiness-report.md` | Task commit e gates. | Atomicidade auditavel. | Campos antigos preservados. |
| `templates/git-decision-report.md` | Worktree lifecycle. | Isolamento auditavel. | Campos antigos preservados. |
| `templates/pr-description.md` | Tasks/commits/ledger/state. | PR revisavel. | Campos antigos preservados. |

### Workflows

| Arquivo | Responsabilidade e motivo | Impacto | Compatibilidade |
| --- | --- | --- | --- |
| `workflows/feature-build.md` | Fluxo completo feature pelo kernel. | Spec→tasks→reviews→release. | Nome preservado. |
| `workflows/bugfix.md` | Reproducao e regression-first. | RED/GREEN vira obrigatorio. | Nome preservado. |
| `workflows/api-refactor.md` | Especializa backend/API. | Contrato/integracao auditados. | Nome preservado. |
| `workflows/backend-change.md` | Backend geral persistente. | Cobre jobs/dados/integracoes. | Novo, reusa skills. |
| `workflows/high-risk-change.md` | Auth/dados/agentes/tools. | Worktree e deep review. | Novo. |
| `workflows/blocked-investigation.md` | Blocker→debug→retomada. | Falhas/hipoteses persistem. | Novo. |
| `workflows/release.md` | `ready_to_ship`→ship/PR. | Release gate e ledger. | Nome preservado. |
| `workflows/agent-workflow.md` | Agentes sob high-risk/kernel. | Plan/runner/reviews separados. | Gates especializados mantidos. |
| `workflows/agent-handoff.md` | Handoff parte do state/next. | Troca de agente segura. | Nome preservado. |
| `workflows/long-conversation-handoff.md` | Compressao subordinada ao state. | Context compaction segura. | Nome preservado. |

### Docs, installers e manutencao

| Arquivo | Responsabilidade e motivo | Impacto | Compatibilidade |
| --- | --- | --- | --- |
| `README.md` | Uso completo do kernel, init, next, estados, reviews e exemplos. | Onboarding P0/P1. | Documenta alias e migracao. |
| `docs/kernel-migration.md` | Migracao e mudancas mais estritas. | Consumidor escolhe opt-in seguro. | Sem quebra silenciosa. |
| `docs/maintenance.md` | Testes obrigatorios para kernel. | Evita drift docs/runtime. | Checklist anterior ampliado. |
| `docs/portability.md` | Shared assets para Codex e Claude Code. | Instalacao reproduzivel. | Fluxo Git/install mantido. |
| `docs/usage-codex.md` | Exemplos das skills P0/P1. | Descoberta no Codex. | Exemplos antigos mantidos. |
| `docs/usage-claude.md` | Exemplos das skills P0/P1. | Descoberta no Claude. | Exemplos antigos mantidos. |
| `installers/install-shared-assets.sh` | Copia shared assets arquivo a arquivo. | Referencias relativas funcionam. | Preserva extras e faz backup. |
| `installers/install-codex.sh` | Chama shared sync para `~/.agents`. | Instala kernel/runtime. | Sem remover skills externas. |
| `installers/install-claude.sh` | Chama shared sync para `~/.claude`. | Instala kernel/runtime. | Sem remover skills externas. |
| `.gitignore` | Ignora bytecode Python. | Tests nao poluem Git. | Regras antigas preservadas. |

### Testes

| Arquivo | Responsabilidade e motivo | Impacto | Compatibilidade |
| --- | --- | --- | --- |
| `tests/__init__.py` | Pacote de testes. | Discovery/import estavel. | `unittest` stdlib. |
| `tests/helpers.py` | Fixtures de projeto/contrato/result/seal. | Reduz duplicacao. | Apenas tests. |
| `tests/test_kernel_initialization.py` | Init, partial init, fase e CLI smoke. | Prova inicializacao segura. | Sem stack nova. |
| `tests/test_kernel_state_machine.py` | Transicoes, guards, seal, paralelo/worktree. | Prova maquina formal. | Sem stack nova. |
| `tests/test_framework_next.py` | planned/executing/reviewing/verifying/inconsistencia. | Prova retomada. | Sem stack nova. |
| `tests/test_task_contracts.py` | Escopo, AC, RED/GREEN e waivers. | Prova task policy. | Sem stack nova. |
| `tests/test_task_reviews.py` | Dois reviews, retorno/correcao/evidence. | Prova disciplina de review. | Sem stack nova. |
| `tests/test_compatibility.py` | Alias, workflows e installer shared. | Prova compatibilidade. | Preserva assets externos. |

## 4. Fluxo final

```text
solicitacao
→ PROJECT/REQUIREMENTS
→ SPEC com ACs
→ workflow-planner gera PLAN
→ TASKS recebe contrato integral
→ plan-quality-checker + seal-plan
→ framework-next seleciona tarefa elegivel
→ task-runner aplica test-policy e retorna implementation_complete
→ self-review registrado
→ spec-compliance-reviewer inspeciona codigo/evidence
→ code-quality-reviewer inspeciona diff/qualidade
→ commit-readiness gera commit atomico quando permitido
→ verifier associa evidence aos ACs e marca tarefa verified
→ framework-next seleciona proxima tarefa
→ sem tarefas: goal coverage/runtime verification
→ ready_to_ship
→ release/PR/handoff
```

Exemplo: `REQ-004` e `REQ-007` produzem `AC-01..03`; o contrato `P1-T03`
autoriza apenas mapper/teste; o resultado registra RED/GREEN/refactor; os reviews
provam spec e qualidade; o ledger liga testes/codigo/reviews aos ACs; o verifier
marca `P1-T03` verified; a proxima tarefa elegivel e retornada por
`framework-next`.

## 5. Verificacoes

### Cobertura dos criterios globais

| # | Criterio | Status | Evidencia |
| --- | --- | --- | --- |
| 1 | Maquina de estados formal | PASS | `kernel/state-machine.md`, `state_machine.py`, testes de transicao |
| 2 | Formato persistente projeto/fase | PASS | templates `project-*`, `phase-*`, init tests |
| 3 | Operacao central de retomada | PASS | `framework-next`, next/CLI tests |
| 4 | Planejamento separado da execucao | PASS | `workflow-planner`, `workflow-runner`, alias test |
| 5 | Contratos formais | PASS | `task-contract.md`, contract validator |
| 6 | Executor consome contrato integral | PASS | `task-runner`, `validate-task/result` |
| 7 | Politica de testes executavel | PASS | `test-policy.yaml`, RED/GREEN/waiver tests |
| 8 | Self-review obrigatorio | PASS | result schema e checklist validator |
| 9 | Review de spec e qualidade separados | PASS | duas skills, templates e validators |
| 10 | Blockers retornam para execucao | PASS | transition/review tests |
| 11 | Evidencia ligada aos ACs | PASS | ledger/event/result/review tests |
| 12 | Estado sobrevive a nova sessao | PASS | filesystem state + CLI resume test |
| 13 | Workflows principais usam kernel | PASS | feature/bugfix/backend/high-risk/debug/release |
| 14 | Assets existentes reutilizados | PASS | skills/workflows integrados, sem duplicacao ampla |
| 15 | Compatibilidade/migracao documentadas | PASS | alias, migration doc, compatibility tests |
| 16 | Testes minimos passam | PASS | 41 tests OK |
| 17 | Verificador atual passa | PASS | `problems: 0` |
| 18 | Sem P2/P3 fora do necessario | PASS | diff limitado a kernel P0/P1 |

### Evidencia final

- `python3 -m unittest discover -s tests -v` → **41 testes, OK**.
- `bash installers/verify-framework.sh` → **problems: 0; verification: ok**.
- `bash -n installers/*.sh scripts/security-check scripts/framework-next` → **OK**.
- `make security:check` → **OK**; sem `.env` tracked ou secrets obvios.
- `git diff --check` e busca por trailing whitespace → **OK**.
- Installer em diretorio temporario → kernel/skills/scripts copiados e asset
  externo preservado.
- CLI em diretorio temporario → init + resume retornaram estado/operacao corretos.

### Falhas encontradas e corrigidas durante a execucao

- Um teste de compatibilidade detectou que `release.md` nao nomeava
  `workflow-runner`; workflow corrigido e suite repetida.
- Onze erros com a mesma causa detectaram escaping incorreto no regex do
  `decision_id`; matcher corrigido e testes especificos/full suite repetidos.
- Self-review detectou fingerprint incluindo `task.status`; canonicalizacao
  corrigida e teste de nao regressao adicionado.

### Limitacoes do ambiente

- Nao ha `package.json`; o security check registrou o skip esperado de npm
  lint/test/audit.
- Nenhum commit/PR foi criado porque nao foi solicitado e o working tree ja
  continha mudancas do usuario.
- O review desta implementacao foi self-review profundo; os testes provam que
  tarefas consumidoras exigem reviewers diferentes do executor.

## 6. Pendencias reais

- As alterações preexistentes do Cursor foram deliberadamente excluídas desta
  branch limpa; nenhum installer Cursor é necessário para P0/P1.
- Review independente humano/por outro agente continua recomendado antes de
  merge por ser uma mudanca de runtime e instalacao. Nao ha blocker tecnico ou
  teste falhando conhecido.
