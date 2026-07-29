# Bugfix Workflow

Use para corrigir bugs com reproducao e verificacao proporcionais.

## Fast

```text
reproduce → fix → targeted regression test → diff review
```

Nao crie `.agent/`, contrato, ledger ou review separado.

## Standard

```text
investigate → short plan → regression test → fix → integrated review
```

Use persistencia apenas se a investigacao atravessar sessoes ou tiver etapas
dependentes.

## Critical

Use `framework-next` → persistent debug session → evidence → spec/contratos →
`workflow-runner`/`task-runner` → RED/GREEN → self-review → spec compliance →
code quality → goal coverage. O kernel P0/P1 permanece integral.

## Saidas

- Sempre: reproducao/causa, fix, teste e diff review.
- `standard`: plano/review leves.
- `critical`: estado, contratos, ledger, reviews separados e transicoes.
