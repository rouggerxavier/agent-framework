# Agent Workflow

Use para criar, refatorar, validar e entregar agentes com prompt, tools, memoria, runtime, guardrails e revisao obrigatoria.

Modo suportado: `critical`, porque este workflow combina multiplas ferramentas,
permissoes, runtime e papeis de review. Ajustes agenticos localizados devem voltar
ao `agent-framework-router` e podem usar `fast`/`standard`.

## Sequencia
1. Use `framework-next` para inicializar/retomar e aplique
   `workflows/high-risk-change.md`.
2. Use `prompt-refiner` para transformar o pedido em objetivo, escopo, inputs, outputs e criterios de aceite.
3. Use `agent-builder` para preencher `templates/agent-design.md`.
4. Use `architecture-decision` se houver decisao relevante de modelo, provider, memoria, runtime ou tool boundary.
5. Use `agent-tool-designer` para tools novas ou alteradas.
6. Use `agent-guardrails-implementer` para input, output, tools, memoria, logs e stop conditions.
7. Use `workflow-planner` com `backend-slice-planner` ou
   `implementation-planner` para gerar contratos integrais.
8. Antes de `planned`, use `plan-quality-checker`.
9. Execute por `workflow-runner` e `task-runner`; preserve configurabilidade e
   evite hardcode de modelo, provider, env vars, paths e tool names.
10. Use `tool-contract-auditor` quando schema, permissao, erro ou side effect de tool mudar.
11. Use `env-gitignore-auditor` quando houver env vars, tokens, logs, traces, caches ou artefatos locais.
12. Use `agent-security-auditor` quando o agente tocar dados sensiveis, fontes nao confiaveis, tools externas ou permissao ampla.
13. Use `agent-eval-planner`, `test-strategy-builder` e `test-confidence-mapper` para definir validacao.
14. Use `tool-runtime-validator` para validar tools com casos reais, falhas e logs.
15. Use `agent-observability-auditor` para logs, traces, metricas, custo e debug readiness.
16. Use `feature-logging-planner` quando a feature puder gerar bugs complexos ou investigacao dificil.
17. Use `agent-runtime-qa` para validar comportamento real do agente completo.
18. Use `code-review-gate` para decidir review deep ou cross-area.
19. Rode `spec-compliance-reviewer` antes da qualidade.
20. Rode `code-quality-reviewer`; ele aciona `agent-code-reviewer` e
    `diff-reviewer` conforme o gate.
21. Use `goal-coverage-verifier` para checar objetivo, guardrails, tools, testes e riscos.
22. Use `git-decision-router` para decidir commit direto, esperar validacao, branch, PR ou deixar unstaged.
23. Use `commit-readiness-checker` antes de qualquer commit.
24. Use `pr-description-builder` quando a decisao for abrir PR.
25. Use `documentation-decision-router` para decidir ADR, README, runbook, agent docs, changelog ou nada.
26. Use `agent-doc-writer` quando a decisao for documentar agente.
27. Use `deadcode-orphan-mapper` quando houver limpeza, prompts/tools antigas ou risco de codigo orfao.
28. Use `agent-optimization-auditor` quando custo, latencia, prompt size, tool calls ou contexto carregado forem relevantes.
29. Use `performance-budget-auditor` quando a mudanca tocar caminho critico, queries, jobs, batch, timeout ou custo operacional.
30. Use `backend-release-packager` ou `handoff-builder` para fechar entrega.

## Gates
- Plan gate: `plan-quality-checker` deve passar ou listar correcoes.
- Kernel gate: estado, contrato integral e evidence ledger sao obrigatorios.
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
- Review gate: spec compliance passa antes de code quality; `code-review-gate`
  seleciona reviewers especializados.
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
