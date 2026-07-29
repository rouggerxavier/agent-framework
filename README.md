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

O framework e rapido por padrao e seleciona uma de tres rotas:

```text
Duvida → fast
Complexidade comprovada → standard
Risco critico comprovado → critical
```

| Modo | Fluxo | Governanca |
| --- | --- | --- |
| `fast` | inspect → implement → targeted verification → diff review | sem `.agent/`, spec, contrato, seal, ledger, reviewers separados ou worktree |
| `standard` | focused grounding → short plan → implement → tests → integrated review | estado opcional, sem seal ou reviews separados |
| `critical` | lifecycle persistente completo | P0/P1 integral |

Use o router como entrada de uma tarefa nova:

```text
$agent-framework-router --fast
Corrija o bug no filtro de imoveis.
```

```text
$agent-framework-router --standard
Implemente o novo endpoint e os testes.
```

```text
$agent-framework-router --critical
Altere o modelo de autenticacao e faca a migration.
```

`--auto` (ou nenhuma flag) deixa o router decidir com preferencia por `fast`.
Toda selecao `standard`/`critical` deve citar fatores concretos. Muitos arquivos,
edge cases teoricos ou a possibilidade abstrata de mais qualidade nao justificam
escalada. O script `scripts/agent-framework-route` expoe a mesma politica de
forma executavel e sem efeitos colaterais.

> O kernel completo e uma capacidade disponivel, nao o fluxo obrigatorio.

Veja `kernel/adaptive-execution-policy.md` para matriz de templates, budget de
verificacao, severidades de review e reuso de contexto.

Quando `standard` realmente precisar sobreviver a outra sessao, a inicializacao
leve cria somente `.agent/STATE.md` e `.agent/PLAN.md`:

```bash
./scripts/framework-next init \
  --project /caminho/do/projeto \
  --name example-project \
  --mode standard
```

`fast` recusa inicializacao persistente. Roadmap, phase spec, contratos, ledger,
reviews separados e plan seal continuam exclusivos do fluxo `critical`.

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
`critical`.

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
