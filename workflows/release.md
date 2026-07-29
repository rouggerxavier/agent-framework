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
10. Registre commit/PR/release no ledger e somente entao solicite `shipped`.
11. Use `context-compressor`/`handoff-builder` para operacao ou suporte.

## Saidas
- Checks executados.
- Blockers e riscos aceitos.
- Plano de rollback.
- Release notes.
- Decisao go/no-go.
- Estado final e referencia de commit/PR/release.
