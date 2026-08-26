# Uso no Claude Code

No Claude Code, chame skills com `/skill-name`.

## Entrada adaptativa

```text
/agent-framework-router --fast Corrija o bug no filtro.
/agent-framework-router --standard Implemente o endpoint e os testes.
/agent-framework-router --critical Altere autenticacao e faca a migration.
```

Sem flag, `--auto` prefere `fast`. Use `framework-next` para retomar trabalho
persistente, nao como entrada obrigatoria de tarefa comum.

## Exemplos

```text
/agent-framework-installer Verifique e sincronize as skills.
```

```text
/agent-builder Planeje ou refatore um agente com tools, memoria, guardrails e validacao.
```

```text
/agent-anti-hardcode-auditor Audite modelo, prompt, tools, paths e env vars hardcoded.
/model-flexibility-auditor Verifique fallback e troca segura de modelo/provider.
/config-surface-auditor Revise env vars, defaults, .env.example e .gitignore.
```

```text
/prompt-refiner Refine este pedido no modo implementation/debug/review/research/runtime-qa.
/agent-prompt-refiner Refine este system prompt com tools, guardrails e evals.
```

```text
/agent-tool-designer Desenhe uma tool com schema, permissao, side effects e erros.
/tool-contract-auditor Audite contrato, timeout, retry, idempotencia e logs da tool.
/tool-runtime-validator Valide a tool em execucao com casos reais e falhas.
```

```text
/agent-guardrails-implementer Especifique guardrails de input, output, tools e logs.
/agent-security-auditor Audite prompt injection, vazamento, tools inseguras e permissoes.
/env-gitignore-auditor Revise .gitignore, .env.example, tokens, logs e artefatos.
```

```text
/agent-eval-planner Planeje evals simples para prompt, tools, fallback e regressao.
/agent-observability-auditor Audite logs, traces, custo, redaction e debug readiness.
/agent-runtime-qa Valide o agente rodando com falhas, fallback e escalacao.
```

```text
/feature-logging-planner Avalie se esta feature precisa de logs e onde logar sem ruido.
```

```text
/code-review-gate Decida se este diff precisa review simples, profundo ou cross-area.
/agent-code-reviewer Revise prompt, tools, guardrails, config, logs, fallback e testes.
```

```text
/ci-throughput-controller Escolha o perfil de CI e diga se posso comecar a proxima unidade.
```

```text
/git-decision-router Decida commit direto, esperar validacao, branch, PR ou unstaged.
/commit-readiness-checker Cheque escopo, testes, secrets e mensagem antes do commit.
/pr-description-builder Gere descricao de PR com evidencias, riscos e rollback.
```

```text
/documentation-decision-router Decida ADR, README, runbook, agent docs, changelog ou nada.
/agent-doc-writer Documente agente com tools, env, guardrails, evals e troubleshooting.
```

```text
/deadcode-orphan-mapper Mapeie codigo morto, prompts/tools orfaos e configs antigas.
/agent-optimization-auditor Audite tokens, latencia, tool calls, cache e model tier.
/performance-budget-auditor Audite latencia, custo, queries, memoria, batch e timeout.
```

```text
/repo-map-builder Mapeie entrypoints, rotas, configs e testes.
```

```text
/task-mode-router Classifique esta tarefa como fast, standard ou critical.
```

```text
/backend-slice-planner Planeje fatias backend verificaveis.
/plan-quality-checker Audite o plano antes de executar.
/goal-coverage-verifier Verifique objetivo, contratos e testes apos implementar.
```

```text
/test-confidence-mapper Mapeie comandos por nivel de confianca.
/dependency-risk-auditor Audite uma nova dependencia antes de instalar.
/persistent-debug-session Abra uma sessao persistente para bug dificil.
```

```text
/data-migration-auditor Audite schema, backfill e rollback.
/docs-sync-auditor Confira README, env vars, API docs e release notes.
/backend-release-packager Monte pacote final com evidencias, riscos e rollback.
```

```text
/api-contract-auditor Revise esta mudanca de endpoint.
/security-privacy-audit Verifique auth, permissoes, logs e secrets.
```

```text
/ui-ux-pro-max-audit Audite esta tela antes do release.
/runtime-qa-audit Valide o fluxo no app em execucao.
```

```text
/handoff-builder Gere um handoff para Codex continuar.
```

## Kernel persistente (`critical`)

```text
/framework-next Retome este projeto sem depender da conversa.
/workflow-planner Planeje esta fase sem implementar.
/workflow-runner Retome o plano pelo STATE.md.
/task-runner Execute o contrato integral da tarefa ativa.
/spec-compliance-reviewer Revise criterios, escopo e evidencias.
/code-quality-reviewer Revise qualidade depois do PASS de spec.
```

Inicializacao e validacao executavel:

```bash
~/agent-framework/scripts/framework-next init --project . --name meu-projeto --mode standard  # STATE + PLAN
~/agent-framework/scripts/framework-next init --project . --name meu-projeto --mode critical
~/agent-framework/scripts/framework-next --project .
```

## Dica

Nova tarefa comum começa pelo `/agent-framework-router` e normalmente usa
`fast`. Use `/framework-next` somente para retomar ou inicializar persistencia
intencional.
