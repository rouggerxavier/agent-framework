# Bugfix Workflow

Use para corrigir bugs com reproducao e verificacao proporcionais.

Em qualquer modo, aplique `test-strategy-builder` e `rubrics/testing.md`:
reaproveite o teste que ja reproduz o defeito ou crie/amplie a regressao faltante.
Busque RED pelo defeito antes da correcao e GREEN depois; falha de setup nao
comprova o bug. Quando isso nao for possivel, declare motivo, evidencia alternativa
e lacuna. Preserve gates e waivers do contrato em `critical`.

## Fast

```text
reproduce → targeted regression test → fix → verify → diff review
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

- Sempre: reproducao/causa, fix, decisao de testes, resultados/lacunas e diff review.
- `standard`: plano/review leves.
- `critical`: estado, contratos, ledger, reviews separados e transicoes.
