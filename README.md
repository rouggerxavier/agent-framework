# agent-framework

Framework pessoal e versionavel de skills, rubrics, workflows, templates e docs para Codex e Claude Code.

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
  skills/
  rubrics/
  workflows/
  templates/
  installers/
  docs/
```

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

## Instalar em ambos

```bash
bash ~/agent-framework/installers/install-all.sh
```

Os installers copiam apenas diretorios em `skills/` que possuem `SKILL.md`. Skills externas que nao existem no framework nao sao removidas. Skills de mesmo nome sao movidas para backup oculto antes de copiar a versao do framework.

## Verificar

```bash
bash ~/agent-framework/installers/verify-framework.sh
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

Use `$task-mode-router` antes de tarefas de backend quando quiser escolher entre `fast`, `quick`, `full` ou `audit`. Ele evita puxar orquestracao completa quando uma rota leve preserva o risco principal.

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
