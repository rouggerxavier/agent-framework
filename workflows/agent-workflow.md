# Agent Workflow

Use para criar, refatorar, validar e entregar agentes com prompt, tools, memoria, runtime, guardrails e revisao obrigatoria.

## Sequencia
1. Use `prompt-refiner` para transformar o pedido em objetivo, escopo, inputs, outputs e criterios de aceite.
2. Use `agent-builder` para preencher `templates/agent-design.md`.
3. Use `architecture-decision` se houver decisao relevante de modelo, provider, memoria, runtime ou tool boundary.
4. Use `agent-tool-designer` para tools novas ou alteradas.
5. Use `agent-guardrails-implementer` para input, output, tools, memoria, logs e stop conditions.
6. Use `backend-slice-planner` ou `implementation-planner` para dividir implementacao.
7. Antes de executar, use `plan-quality-checker`.
8. Durante a implementacao, preserve configurabilidade e evite hardcode de modelo, provider, env vars, paths e tool names.
9. Use `tool-contract-auditor` quando schema, permissao, erro ou side effect de tool mudar.
10. Use `env-gitignore-auditor` quando houver env vars, tokens, logs, traces, caches ou artefatos locais.
11. Use `agent-security-auditor` quando o agente tocar dados sensiveis, fontes nao confiaveis, tools externas ou permissao ampla.
12. Use `agent-eval-planner`, `test-strategy-builder` e `test-confidence-mapper` para definir validacao.
13. Use `tool-runtime-validator` para validar tools com casos reais, falhas e logs.
14. Use `agent-observability-auditor` para logs, traces, metricas, custo e debug readiness.
15. Use `feature-logging-planner` quando a feature puder gerar bugs complexos ou investigacao dificil.
16. Use `agent-runtime-qa` para validar comportamento real do agente completo.
17. Use `code-review-gate` para decidir review simples, profundo ou cross-area.
18. Use `agent-code-reviewer` quando o diff tocar agente, prompt, tools, guardrails, config, observabilidade ou fallback.
19. Use `diff-reviewer` para review geral quando `agent-code-reviewer` nao for o alvo principal.
20. Use `goal-coverage-verifier` para checar objetivo, guardrails, tools, testes e riscos.
21. Use `git-decision-router` para decidir commit direto, esperar validacao, branch, PR ou deixar unstaged.
22. Use `commit-readiness-checker` antes de qualquer commit.
23. Use `pr-description-builder` quando a decisao for abrir PR.
24. Use `documentation-decision-router` para decidir ADR, README, runbook, agent docs, changelog ou nada.
25. Use `agent-doc-writer` quando a decisao for documentar agente.
26. Use `deadcode-orphan-mapper` quando houver limpeza, prompts/tools antigas ou risco de codigo orfao.
27. Use `agent-optimization-auditor` quando custo, latencia, prompt size, tool calls ou contexto carregado forem relevantes.
28. Use `performance-budget-auditor` quando a mudanca tocar caminho critico, queries, jobs, batch, timeout ou custo operacional.
29. Use `backend-release-packager` ou `handoff-builder` para fechar entrega.

## Gates
- Plan gate: `plan-quality-checker` deve passar ou listar correcoes.
- Tool design gate: tool nova precisa de `agent-tool-designer`.
- Tool contract gate: mudanca de schema, permissao, erro ou side effect precisa de `tool-contract-auditor`.
- Guardrails gate: agente com tools, memoria ou usuario externo precisa de `agent-guardrails-implementer`.
- Security gate: se tocar secrets, env, auth, logs, dados ou tools externas, use `security-privacy-audit`.
- Agent security gate: se houver fonte nao confiavel, tool externa ou dados sensiveis, use `agent-security-auditor`.
- Env gate: env vars, tokens, logs, traces ou caches precisam de `env-gitignore-auditor`.
- Dependency gate: se adicionar pacote, use `dependency-risk-auditor`.
- Eval gate: agente recorrente, prompt critico ou model migration precisa de `agent-eval-planner`.
- Observability gate: agente com tools/provider externo precisa de `agent-observability-auditor`.
- Logging gate: feature com fluxo complexo, side effect, integracao externa, auth, dados, job, agent/tool call ou fallback precisa de `feature-logging-planner`.
- Tool runtime gate: tool com side effect, rede, auth ou provider externo precisa de `tool-runtime-validator`.
- Runtime gate: agente com tool/runtime precisa de `agent-runtime-qa`.
- Review gate: `code-review-gate` e obrigatorio antes de pronto; ele decide `diff-reviewer`, `agent-code-reviewer` ou review cross-area.
- Git gate: `git-decision-router` decide commit/PR; `commit-readiness-checker` e obrigatorio antes de commit.
- Documentation gate: `documentation-decision-router` decide se precisa ADR, README, runbook, agent docs, changelog ou nada.
- Cleanup gate: limpeza ou refatoracao ampla precisa de `deadcode-orphan-mapper` antes de remover.
- Optimization gate: agente com custo/latencia/contexto alto precisa de `agent-optimization-auditor`.
- Performance gate: caminho critico, query, job, batch, timeout ou custo operacional precisa de `performance-budget-auditor`.

## Saidas
- Agent design.
- Plano de implementacao.
- Evidencias de teste/runtime QA.
- Achados de review e correcoes.
- Pacote final ou handoff.
