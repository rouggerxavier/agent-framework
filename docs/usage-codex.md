# Uso no Codex

No Codex, chame skills com `$skill-name`.

## Exemplos

```text
$agent-framework-installer Verifique e instale o framework neste computador.
```

```text
$agent-builder Planeje ou refatore um agente com tools, memoria, guardrails e validacao.
```

```text
$agent-anti-hardcode-auditor Audite modelo, prompt, tools, paths e env vars hardcoded.
$model-flexibility-auditor Verifique fallback e troca segura de modelo/provider.
$config-surface-auditor Revise env vars, defaults, .env.example e .gitignore.
```

```text
$prompt-refiner Refine este pedido no modo implementation/debug/review/research/runtime-qa.
$agent-prompt-refiner Refine este system prompt com tools, guardrails e evals.
```

```text
$agent-tool-designer Desenhe uma tool com schema, permissao, side effects e erros.
$tool-contract-auditor Audite contrato, timeout, retry, idempotencia e logs da tool.
$tool-runtime-validator Valide a tool em execucao com casos reais e falhas.
```

```text
$agent-guardrails-implementer Especifique guardrails de input, output, tools e logs.
$agent-security-auditor Audite prompt injection, vazamento, tools inseguras e permissoes.
$env-gitignore-auditor Revise .gitignore, .env.example, tokens, logs e artefatos.
```

```text
$agent-eval-planner Planeje evals simples para prompt, tools, fallback e regressao.
$agent-observability-auditor Audite logs, traces, custo, redaction e debug readiness.
$agent-runtime-qa Valide o agente rodando com falhas, fallback e escalacao.
```

```text
$feature-logging-planner Avalie se esta feature precisa de logs e onde logar sem ruido.
```

```text
$code-review-gate Decida se este diff precisa review simples, profundo ou cross-area.
$agent-code-reviewer Revise prompt, tools, guardrails, config, logs, fallback e testes.
```

```text
$git-decision-router Decida commit direto, esperar validacao, branch, PR ou unstaged.
$commit-readiness-checker Cheque escopo, testes, secrets e mensagem antes do commit.
$pr-description-builder Gere descricao de PR com evidencias, riscos e rollback.
```

```text
$documentation-decision-router Decida ADR, README, runbook, agent docs, changelog ou nada.
$agent-doc-writer Documente agente com tools, env, guardrails, evals e troubleshooting.
```

```text
$deadcode-orphan-mapper Mapeie codigo morto, prompts/tools orfaos e configs antigas.
$agent-optimization-auditor Audite tokens, latencia, tool calls, cache e model tier.
$performance-budget-auditor Audite latencia, custo, queries, memoria, batch e timeout.
```

```text
$workflow-orchestrator Planeje esta feature com skills, modelo, effort e riscos.
```

```text
$task-mode-router Classifique esta tarefa de backend como fast, quick, full ou audit.
```

```text
$backend-slice-planner Planeje fatias backend verificaveis.
$plan-quality-checker Audite o plano antes de executar.
$goal-coverage-verifier Verifique objetivo, contratos e testes apos implementar.
```

```text
$test-confidence-mapper Mapeie comandos por nivel de confianca.
$dependency-risk-auditor Audite uma nova dependencia antes de instalar.
$persistent-debug-session Abra uma sessao persistente para bug dificil.
```

```text
$data-migration-auditor Audite schema, backfill e rollback.
$docs-sync-auditor Confira README, env vars, API docs e release notes.
$backend-release-packager Monte pacote final com evidencias, riscos e rollback.
```

```text
$project-context-loader Leia o repo e resuma stack, comandos e padroes.
$implementation-planner Crie plano por fases para a feature.
```

```text
$bug-repro-lab Reproduza e corrija este bug.
$test-strategy-builder Defina teste de regressao.
$diff-reviewer Revise o diff antes do merge.
```

```text
$context-compressor Comprima esta conversa com estado atual, riscos e prompt de retomada.
```

## Dica

Use uma skill por etapa. Para backend, comece com `$task-mode-router`; para tarefas grandes ja confirmadas, use `$workflow-orchestrator`.
