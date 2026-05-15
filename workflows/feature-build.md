# Feature Build Workflow

Use para construir feature de forma incremental e verificavel.

## Sequencia
1. Use `project-context-loader` para contexto local.
2. Use `implementation-planner` para fases, arquivos e testes.
3. Use `architecture-decision` se houver escolha tecnica relevante.
4. Implemente fase por fase, mantendo escopo pequeno.
5. Use `test-strategy-builder` para cobertura.
6. Use `runtime-qa-audit` para fluxo real quando houver UI/app.
7. Use `release-verifier` antes de entrega.

## Saidas
- Plano por fases.
- Mudancas implementadas.
- Testes e QA executados.
- Riscos e pendencias.
- Handoff ou release notes quando necessario.
