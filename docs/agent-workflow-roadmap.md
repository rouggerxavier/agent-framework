# Agent Workflow Roadmap

## Objetivo
Criar um pacote de skills e workflows para construir, refatorar, validar e entregar agentes com menos hardcode, menos engessamento de modelo, mais seguranca e revisao obrigatoria.

## Principios
- Agente deve ser modular: prompt, tools, memoria, runtime, validacao e seguranca separados.
- Evitar hardcode de modelo, provider, path, tool name, prompt fixo e env var.
- Toda implementacao relevante deve passar por code review antes de ser considerada pronta.
- Guardrails e seguranca entram antes da release, nao depois do incidente.
- Runtime validation deve confirmar comportamento real, nao apenas que o codigo compila.

## O que ja existe e deve ser reaproveitado
| Necessidade | Asset existente | Gap |
| --- | --- | --- |
| Refinar prompt bruto | `prompt-refiner` | Falta especializacao por tipo de acao e por agente. |
| Planejar implementacao | `backend-slice-planner`, `implementation-planner` | Falta workflow especifico de agente. |
| Revisar diff | `diff-reviewer` | Falta obrigatoriedade no workflow. |
| QA runtime | `runtime-qa-audit` | Falta checklist especifico para agente/tools. |
| Seguranca | `security-privacy-audit`, `dependency-risk-auditor` | Falta guardrails de agente e env/gitignore. |
| Testes | `test-strategy-builder`, `test-confidence-mapper` | Falta matriz especifica para agentes. |
| Release | `backend-release-packager`, `release-verifier` | Falta pacote final de agente. |
| Arquitetura | `architecture-decision` | Falta decisao anti-hardcode/anti-model-lock. |
| Map loader | `repo-map-builder`, `project-context-loader` | Falta modo deadcode/orphan-code. |

## Etapa 1: Nucleo de Criacao de Agente
Criar primeiro porque vira entrada para todo o resto.

### Criar
- `agent-builder`
  - Criado em `skills/agent-builder`.
  - Planeja e cria agentes com objetivo, entradas, saidas, tools, memoria, runtime, guardrails e validacao.
- `agent-workflow`
  - Criado em `workflows/agent-workflow.md`.
  - Workflow: refine prompt -> agent design -> tool design -> guardrails -> implement -> runtime QA -> code review -> package.
- `agent-design-template`
  - Criado em `templates/agent-design.md`.
  - Template com: objetivo, users/tasks, prompt, tools, state, memory, model policy, guardrails, tests, failure modes.

### Reaproveitar
- `prompt-refiner`
- `architecture-decision`
- `backend-slice-planner`
- `test-strategy-builder`

## Etapa 2: Anti-Hardcode e Anti-Engessamento
Criar cedo porque corrige um erro comum em agentes: acoplar tudo a um modelo, provider ou prompt fixo.

### Criar
- `agent-anti-hardcode-auditor`
  - Criado em `skills/agent-anti-hardcode-auditor`.
  - Procura hardcode de model IDs, provider IDs, URLs, env names, tool names, prompt snippets, paths, magic constants e feature flags.
- `model-flexibility-auditor`
  - Criado em `skills/model-flexibility-auditor`.
  - Verifica se o agente funciona com politica de modelo/provider configuravel, fallback, capability routing e limites claros.
- `config-surface-auditor`
  - Criado em `skills/config-surface-auditor`.
  - Revisa configs, env vars, defaults, overrides, secrets e `.gitignore`.

### Reaproveitar
- `model-routing`
- `security-privacy-audit`
- `dependency-risk-auditor`
- `docs-sync-auditor`

## Etapa 3: Prompt Refinement Por Tipo de Acao
Seu `prompt-refiner` existe, mas deve virar familia ou ganhar modo especializado.

### Criar ou atualizar
- Atualizar `prompt-refiner` com modos:
  - Atualizado em `skills/prompt-refiner`.
  - `implementation`
  - `debug`
  - `review`
  - `research`
  - `agent-build`
  - `runtime-qa`
  - `security-audit`
- Criar template `action-prompt-package.md`
  - Criado em `templates/action-prompt-package.md`.
  - Inclui objetivo, contexto minimo, constraints, tools permitidas, stop conditions, output contract e verification.

### Opcional criar
- `agent-prompt-refiner`
  - Criado em `skills/agent-prompt-refiner`.
  - Especializado em prompts de sistema/agente, tool instructions, guardrails e exemplos negativos.

## Etapa 4: Tools Para Agente
Agentes falham muito por tools mal definidas: schema frouxo, side effects, permissao ampla ou erro sem contrato.

### Criar
- `agent-tool-designer`
  - Criado em `skills/agent-tool-designer`.
  - Define tools com nome, schema, permissao, side effects, erros, idempotencia e exemplos.
- `tool-contract-auditor`
  - Criado em `skills/tool-contract-auditor`.
  - Audita schemas, payloads, status/erro, permissao, timeout, retry, idempotencia e observabilidade.
- `tool-runtime-validator`
  - Criado em `skills/tool-runtime-validator`.
  - Valida tools em execucao com casos reais, erros e logs.

### Reaproveitar
- `api-contract-auditor`
- `runtime-qa-audit`
- `security-privacy-audit`
- `test-confidence-mapper`

## Etapa 5: Guardrails e Seguranca
Aqui entram suas lacunas de seguranca: `.gitignore`, env, secrets, permissao, logs e prompt injection.

### Criar
- `agent-guardrails-implementer`
  - Criado em `skills/agent-guardrails-implementer`.
  - Implementa ou especifica guardrails: input validation, output constraints, permissions, escalation, refusal/stop conditions e audit logs.
- `agent-security-auditor`
  - Criado em `skills/agent-security-auditor`.
  - Audita agentes contra prompt injection, data exfiltration, unsafe tool use, secret leakage, logs sensiveis e permissao excessiva.
- `env-gitignore-auditor`
  - Criado em `skills/env-gitignore-auditor`.
  - Checa `.gitignore`, `.env.example`, secrets, config local, tokens, logs e artefatos gerados.

### Reaproveitar
- `security-privacy-audit`
- `dependency-risk-auditor`
- `docs-sync-auditor`

## Etapa 6: Runtime Validation e QA de Agente
Mais especifico que QA de app: precisa validar comportamento do agente, tools, fallback, erro e custo.

### Criar
- `agent-runtime-qa`
  - Criado em `skills/agent-runtime-qa`.
  - Valida o agente rodando: happy path, bad input, missing env, tool failure, timeout, retry, fallback model e escalation.
- `agent-eval-planner`
  - Criado em `skills/agent-eval-planner`.
  - Define evals simples: casos, expected behavior, allowed variance, failure modes e regressao.
- `agent-observability-auditor`
  - Criado em `skills/agent-observability-auditor`.
  - Checa logs, traces, metrics, cost tracking, prompt/tool audit e debug readiness.

### Reaproveitar
- `runtime-qa-audit`
- `test-strategy-builder`
- `test-confidence-mapper`
- `persistent-debug-session`

## Etapa 7: Logging Proporcional de Feature
Toda feature nova com risco de bug complexo deve avaliar se precisa de logs. O objetivo e cobrir o fluxo ponta a ponta quando faz sentido, sem criar log em cada linha nem vazar dados.

### Criar
- `feature-logging-planner`
  - Criado em `skills/feature-logging-planner`.
  - Avalia se a feature precisa de logs, define pontos de log, nivel, campos, correlation id, redaction, volume e verificacao runtime.

### Reaproveitar
- `agent-observability-auditor`
- `runtime-qa-audit`
- `security-privacy-audit`
- `persistent-debug-session`

### Quando aplicar como gate
- Fluxo multi-etapa, estado, permissao, dados ou side effects.
- Integracao externa, fila, job, cache, retry, fallback, agente ou tool call.
- Bug seria dificil de investigar apenas com stack trace ou teste automatizado.
- Logs existentes nao respondem "onde falhou, para quem, por que e com qual correlacao".

### Quando nao logar
- Mudanca trivial, copy/docs/UI simples ou fluxo sem ambiguidade operacional.
- Log nao responde pergunta de debug, auditoria ou operacao.
- Log proposto aumenta ruido, cardinalidade ou risco de vazamento sem beneficio claro.

## Etapa 8: Code Review Obrigatorio
Transformar revisao em gate do workflow, com profundidade proporcional.

### Criar
- `code-review-gate`
  - Criado em `skills/code-review-gate`.
  - Decide se precisa review simples, profundo ou cross-area.
  - Bloqueia conclusao se diff toca agente, auth, secrets, tools, dados, model routing ou runtime behavior.
- `agent-code-reviewer`
  - Criado em `skills/agent-code-reviewer`.
  - Especializa `diff-reviewer` para agentes: prompt, tools, guardrails, config, observabilidade e fallback.

### Reaproveitar
- `diff-reviewer`
- `goal-coverage-verifier`
- `plan-quality-checker`

## Etapa 9: Git, Commit e Fases
Voce quer criterio claro para commit direto vs esperar validacao.

### Criar
- `git-decision-router`
  - Criado em `skills/git-decision-router`.
  - Decide: commit direto, esperar QA, esperar review, criar branch, abrir PR, ou apenas deixar unstaged.
- `commit-readiness-checker`
  - Criado em `skills/commit-readiness-checker`.
  - Checa diff, testes, docs, secrets, escopo e mensagem antes de commit.
- `pr-description-builder`
  - Criado em `skills/pr-description-builder`.
  - Gera PR com escopo, evidencias, riscos, rollback e screenshots/logs quando aplicavel.

### Regras iniciais
- Commit direto: docs/copy/config trivial, teste/verificacao simples, sem contrato.
- Esperar validacao: agente, tools, runtime behavior, env, auth, dados, security ou dependencia.
- Review profundo: model routing, guardrails, tool permissions, prompt injection, secrets, external integrations.

## Etapa 10: Documentacao e ADR
Criar docs somente quando o custo de redescobrir for maior que o custo de manter doc.

### Criar
- `documentation-decision-router`
  - Criado em `skills/documentation-decision-router`.
  - Decide entre ADR, README update, runbook, changelog, prompt/package docs ou nada.
- `agent-doc-writer`
  - Criado em `skills/agent-doc-writer`.
  - Documenta agente: objetivo, tools, config, env, guardrails, evals, runbook e troubleshooting.

### Reaproveitar
- `docs-sync-auditor`
- `architecture-decision`
- `backend-release-packager`

### Quando ADR e necessario
- Decisao dificil de reverter.
- Troca de modelo/provider/runtime.
- Nova politica de guardrail.
- Mudanca de permissao de tool.
- Nova arquitetura de memoria/state.

## Etapa 11: Deadcode, Codigo Orfao e Otimizacao
Separar map loader geral de auditorias de limpeza e performance.

### Criar
- `deadcode-orphan-mapper`
  - Criado em `skills/deadcode-orphan-mapper`.
  - Procura exports nao usados, rotas mortas, jobs sem trigger, configs antigas, prompts sem chamada, tools registradas mas nao usadas.
- `agent-optimization-auditor`
  - Criado em `skills/agent-optimization-auditor`.
  - Otimiza token, latencia, tool calls, retries, cache, prompt size, model tier e contexto carregado.
- `performance-budget-auditor`
  - Criado em `skills/performance-budget-auditor`.
  - Cobre backend e agente: latencia, custo, memory, query, batch, timeout.

### Reaproveitar
- `repo-map-builder`
- `model-routing`
- `test-confidence-mapper`
- `runtime-qa-audit`

## Ordem Recomendada de Implementacao
1. `agent-builder`
2. `agent-workflow`
3. `agent-anti-hardcode-auditor`
4. `agent-tool-designer`
5. `agent-guardrails-implementer`
6. `agent-security-auditor`
7. `agent-runtime-qa`
8. `feature-logging-planner`
9. `code-review-gate`
10. `git-decision-router`
11. `documentation-decision-router`
12. `deadcode-orphan-mapper`
13. `agent-optimization-auditor`

## Primeiro Lote Sugerido
Criar estas 4 primeiro:
- `agent-builder` (criado)
- `agent-anti-hardcode-auditor` (criado)
- `agent-guardrails-implementer` (criado)
- `code-review-gate` (criado)

Elas atacam a base: criar agente melhor, evitar hardcode, implementar seguranca minima e impedir entrega sem review.
