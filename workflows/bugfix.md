# Bugfix Workflow

Use para corrigir bugs com reproducao, causa provavel, fix minimo e regressao.

## Sequencia
1. Rode `project-context-loader` se repo ou comandos nao estiverem claros.
2. Use `bug-repro-lab` para registrar esperado, obtido e reproducao.
3. Leia apenas arquivos ligados ao fluxo afetado.
4. Aplique a menor correcao coerente com o sistema.
5. Use `test-strategy-builder` para escolher regressao.
6. Use `diff-reviewer` antes de finalizar.
7. Use `context-compressor` se outro agente for continuar.

## Saidas
- Causa provavel com evidencia.
- Fix aplicado ou recomendado.
- Teste de regressao ou justificativa.
- Comandos executados e resultado.
- Riscos restantes.
