# Task Memory

Limite padrao: 6000 caracteres. Atualize com `$skill-evolution-loop`.

## Regras
- Nao salve secrets, tokens, dados pessoais sensiveis ou detalhes privados desnecessarios.
- Cada entrada representa um padrao recorrente, nao uma tarefa isolada.
- Conte ocorrencias distintas; repeticoes dentro da mesma tentativa nao contam.
- Ao passar do limite, compacte exemplos antigos e preserve padroes com maior contagem.

## Entradas
| Chave | Contagem | Ultima vez | Evidencia curta | Decisao | Asset |
| --- | ---: | --- | --- | --- | --- |
| evolve-agent-framework | 1 | 2026-06-07 | Usuario pediu analise do repo, padroes, novas skills e mecanismo de criacao automatica por recorrencia. | observar | skills/skill-evolution-loop |
| route-task-mode | 1 | 2026-06-07 | Analise inspirada em GSD indicou necessidade de escolher fast, quick, full ou audit para reduzir overhead e token. | criar skill | skills/task-mode-router |
| backend-gsd-lite-core | 1 | 2026-06-07 | Usuario pediu prioridade 1 inteira: plano backend em fatias, auditoria de plano e verificacao de cobertura. | criar skills | skills/backend-slice-planner, skills/plan-quality-checker, skills/goal-coverage-verifier |
| backend-gsd-lite-confidence | 1 | 2026-06-07 | Usuario pediu prioridade 2: confianca de testes, auditoria de dependencias e debug persistente para backend. | criar skills | skills/test-confidence-mapper, skills/dependency-risk-auditor, skills/persistent-debug-session |
| backend-gsd-lite-release | 1 | 2026-06-07 | Usuario pediu prioridade 3: pacote de release backend, docs sync e auditoria de data migration. | criar skills | skills/backend-release-packager, skills/docs-sync-auditor, skills/data-migration-auditor |
| agent-workflow-core | 1 | 2026-06-07 | Usuario pediu etapa 1 para criacao/refatoracao de agentes: builder, workflow e template de design. | criar assets | skills/agent-builder, workflows/agent-workflow.md, templates/agent-design.md |
| agent-anti-hardcode-core | 1 | 2026-06-07 | Usuario pediu etapa 2: anti-hardcode, anti-engessamento de modelo e superficie de configuracao para agentes. | criar skills | skills/agent-anti-hardcode-auditor, skills/model-flexibility-auditor, skills/config-surface-auditor |
| action-prompt-refinement | 1 | 2026-06-07 | Usuario pediu etapa 3: prompt-refiner por tipo de acao e refinamento especializado para prompts de agentes. | criar/update | skills/prompt-refiner, skills/agent-prompt-refiner, templates/action-prompt-package.md |
| agent-tool-lifecycle | 1 | 2026-06-07 | Usuario pediu etapa 4: design, auditoria de contrato e validacao runtime para tools de agentes. | criar skills | skills/agent-tool-designer, skills/tool-contract-auditor, skills/tool-runtime-validator |
| agent-guardrails-security | 1 | 2026-06-07 | Usuario pediu etapa 5: guardrails, seguranca agentica e auditoria env/gitignore/secrets. | criar skills | skills/agent-guardrails-implementer, skills/agent-security-auditor, skills/env-gitignore-auditor |
| agent-runtime-evals-observability | 1 | 2026-06-07 | Usuario pediu etapa 6: QA runtime de agente, planejamento de evals e auditoria de observabilidade/debug. | criar skills | skills/agent-runtime-qa, skills/agent-eval-planner, skills/agent-observability-auditor |
| feature-logging-coverage | 1 | 2026-06-07 | Usuario pediu etapa extra para avaliar, criar e manter logs proporcionais em features com risco de bugs complexos. | criar skill | skills/feature-logging-planner, templates/feature-logging-plan.md |
| agent-code-review-gate | 1 | 2026-06-08 | Usuario pediu ir para etapa 7; como logging virou etapa 7, etapa pendente agora e code review obrigatorio/proporcional. | criar skills | skills/code-review-gate, skills/agent-code-reviewer |
| git-commit-pr-flow | 1 | 2026-06-08 | Usuario pediu etapa 8 apos code review; etapa pendente e criterio para commit direto, validacao, branch e PR. | criar skills | skills/git-decision-router, skills/commit-readiness-checker, skills/pr-description-builder |
| documentation-adr-agent-docs | 1 | 2026-06-08 | Usuario pediu etapa 9 apos git; etapa pendente e decidir documentacao/ADR e escrever docs de agente. | criar skills | skills/documentation-decision-router, skills/agent-doc-writer |
| deadcode-optimization-performance | 1 | 2026-06-08 | Usuario pediu etapa 10 apos docs; etapa pendente e deadcode/orfaos, otimizacao de agente e performance budget. | criar skills | skills/deadcode-orphan-mapper, skills/agent-optimization-auditor, skills/performance-budget-auditor |
