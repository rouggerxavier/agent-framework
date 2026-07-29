# Feature Build Workflow

Use para construir feature de forma incremental, persistente e verificavel pelo
kernel.

## Sequencia
1. `framework-next`: inicialize `.agent/` com seguranca ou retome o estado.
2. Route: use `agent-framework-router`.
3. Ground: use `project-context-loader` e persista fatos/unknowns em `CONTEXT.md`.
4. Discuss: resolva incertezas materiais e registre decisoes.
5. Specify: congele requisitos, escopo e aceite em `SPEC.md`.
6. Plan: use `workflow-planner`, `execution-plan-builder` ou planner especializado.
7. Crie o grafo e contratos integrais em `TASKS.md`.
8. Use `test-strategy-builder` e `code-review-gate` para testes/gates por tarefa.
9. Audit: `plan-quality-checker` deve passar antes de `planned`.
10. Isole com branch/worktree conforme risco e conflitos.
11. Execute uma tarefa elegivel por `workflow-runner` → `task-runner`.
12. Registre resultado, falhas e self-review em `EVIDENCE.md`.
13. Review 1: `spec-compliance-reviewer`.
14. Review 2: `code-quality-reviewer`, com reviewers especializados do gate.
15. Use `commit-readiness-checker` e gere commit atomico quando o ambiente permitir.
16. Repita pela proxima operacao retornada por `framework-next`.
17. Use `goal-coverage-verifier` e `runtime-qa-audit` na fase.
18. `verifying → ready_to_ship` somente com aceite, checks, blockers e waivers validos.
19. Use `release-verifier`, `git-decision-router` e `pr-description-builder`.

## Saidas
- Estado, spec, plano, contratos e contexto persistentes.
- Commits/resultados por tarefa e ledger de evidencia.
- Dois reviews independentes por tarefa.
- Verificacao de objetivo/runtime e release gate.
- PR, release ou handoff com proxima operacao.

## Gates

- Planejamento e execucao usam papeis separados.
- Correcao de review invalida aprovacoes afetadas.
- Testes passando nao substituem conformidade; review nao substitui testes.
- Plano muda somente por decisao, revisao e novo plan gate.
