# Release Workflow

Use para preparar, verificar e comunicar uma release.

## Sequencia
1. Confirme escopo e mudancas.
2. Use `test-strategy-builder` para cobertura final.
3. Use `runtime-qa-audit` para smoke test dos fluxos criticos.
4. Use `security-privacy-audit` se tocar auth, dados, secrets ou permissoes.
5. Use `release-verifier` para decisao go/no-go.
6. Preencha `templates/release-checklist.md`.
7. Use `handoff-builder` para operacao ou suporte.

## Saidas
- Checks executados.
- Blockers e riscos aceitos.
- Plano de rollback.
- Release notes.
- Decisao go/no-go.
