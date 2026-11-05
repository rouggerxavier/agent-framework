# Feature Build Workflow

Use para construir feature com caminho proporcional ao modo selecionado.

Em qualquer modo, aplique `test-strategy-builder` antes de implementar: inspecione
cobertura existente e decida criar, ampliar, reaproveitar ou justificar nenhum
teste novo conforme `rubrics/testing.md`. Na revisao final, avalie a utilidade dos
testes criados ou afetados. Preserve gates do contrato em `critical`.

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

- `fast`: mudanca, decisao de testes, verificacao direcionada e diff revisado.
- `standard`: plano curto, decisao de testes, resultados e review integrado.
- `critical`: todos os artefatos, gates e reviews P0/P1.

## Gates

- Escalada exige evidencia concreta.
- Correcao localizada reabre somente criterios/revisoes afetados.
- Plan seal e separacao formal de papeis pertencem a `critical`.
