# Blocked Investigation Workflow

Use quando um blocker exige investigacao persistente antes de retomar a fase.

## Sequencia

1. Registre blocker, evidencia, `blocked_from`, owner e condicoes de desbloqueio.
2. Transicione para `blocked` e abra `persistent-debug-session`.
3. Registre hipoteses, evidencia a favor/contra e experimentos pequenos.
4. Depois de cada experimento, registre comando, resultado e decisao no ledger.
5. Quando houver causa, proponha fix minimo e teste de regressao.
6. Resolva ou escale o blocker; nunca o apague sem evidencia.
7. Revalide Git, contexto e artefatos.
8. Retome exclusivamente o estado registrado em `blocked_from`.

## Saidas

- Blocker e sessao de debug persistentes.
- Experimentos/falhas preservados no ledger.
- Condicao de retomada satisfeita ou escalacao explicita.
