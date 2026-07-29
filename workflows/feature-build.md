# Feature Build Workflow

Use para construir feature com caminho proporcional ao modo selecionado.

## Fast

```text
route → inspect relevant files → implement → targeted tests → diff review
```

Nao inicialize `.agent/`, nao gere spec/contrato/ledger e nao use reviewers
separados.

## Standard

```text
route → focused grounding → short plan → implement → tests → integrated review
```

Estado e worktree sao opcionais por necessidade concreta. Nao use plan seal nem
reviews separados.

## Critical

Use `framework-next` → ground → discuss → spec → `workflow-planner` → plan gate
e seal → contratos → `workflow-runner`/`task-runner` → self-review → spec
compliance → code quality → evidence → goal/runtime/release verification.

## Saidas

- `fast`: mudanca, teste direcionado e diff revisado.
- `standard`: plano curto, testes e review integrado.
- `critical`: todos os artefatos, gates e reviews P0/P1.

## Gates

- Escalada exige evidencia concreta.
- Correcao localizada reabre somente criterios/revisoes afetados.
- Plan seal e separacao formal de papeis pertencem a `critical`.
