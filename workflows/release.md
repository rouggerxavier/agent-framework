# Release Workflow

Use para promover `ready_to_ship` para entrega, PR ou release sem perder
evidencia e rollback.

## Sequencia
1. Use `framework-next`; `workflow-runner` coordena o fluxo e prossegue somente
   em `ready_to_ship`.
2. Confirme escopo, task commits, reviews, ledger e commit verificado.
3. Use `goal-coverage-verifier` e `test-strategy-builder` para lacunas finais.
4. Rode `runtime-qa-audit` nos fluxos criticos e registre resultado.
5. Use gates especializados de seguranca, dados, API e dependencia conforme risco.
6. Use `release-verifier`; blocker retorna a `verifying` ou `blocked`.
7. Preencha `templates/release-checklist.md` com evidencia e rollback.
8. Use `git-decision-router`: commit/branch/PR/handoff conforme ambiente.
9. Antes de commit use `commit-readiness-checker`; antes de PR use
   `pr-description-builder`.
10. Registre commit/PR/release no ledger, passe o gate de release com
    `framework-next gate-status --gate release --to passed`, citando decisao e
    evidencia, e somente entao solicite `shipped`.
11. Para abrir a proxima fase ja contratada, use
    `framework-next activate-phase`; veja `workflows/phase-rotation.md`.
12. Use `context-compressor`/`handoff-builder` para operacao ou suporte.

## Gate de release

`ready_to_ship -> shipped` le `gates.release`. O gate so chega a `passed` com
decisao registrada em `DECISIONS.md` e evidencia que resolva para um arquivo
real da fase ativa:

```bash
framework-next gate-status \
  --gate release --to passed \
  --decision D-043 \
  --evidence ".agent/phases/<slug>/EVIDENCE.md#release" \
  --actor releaser \
  --note "PR #25 mergeado, CI 5/5 verde"
```

O comando nao executa a transicao. Passar o gate e dar `shipped` continuam dois
atos deliberados.

`shipped` significa fase integrada e encerrada no ciclo controlado — nao
liberacao em producao. Blockers externos de producao permanecem registrados e
abertos sem reabrir a fase concluida.

## Saidas
- Checks executados.
- Blockers e riscos aceitos.
- Plano de rollback.
- Release notes.
- Decisao go/no-go.
- Estado final e referencia de commit/PR/release.
