# API Refactor Workflow

Use para refatorar endpoints, schemas, eventos ou clientes sem quebrar consumidores.

## Sequencia
1. Use `repo-map-builder` para localizar rotas, controllers, schemas, clients e testes.
2. Use `api-contract-auditor` para mapear contrato atual e consumidores.
3. Defina estrategia: compatibilidade, nova versao, adaptador ou migracao.
4. Planeje testes com `test-strategy-builder`.
5. Implemente em passos pequenos, preservando comportamento observavel.
6. Revise com `diff-reviewer` usando `rubrics/api-contract.md`.
7. Use `release-verifier` se houver deploy.

## Saidas
- Contratos afetados.
- Plano de compatibilidade ou migracao.
- Mudancas por fase.
- Testes de contrato.
- Riscos e comunicacao necessaria.
