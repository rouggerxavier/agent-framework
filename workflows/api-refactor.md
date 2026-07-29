# API Refactor Workflow

Use para refatorar endpoints, schemas, eventos ou clientes sem quebrar
consumidores. Este workflow especializa `backend-change.md`.

## Sequencia
1. Use `framework-next`, `project-context-loader` e `repo-map-builder`.
2. Use `api-contract-auditor` para mapear contrato e consumidores.
3. Persista estrategia de compatibilidade, versao, adaptador ou migracao como decisao.
4. Use `workflow-planner` e contratos `change_type: api_contract`.
5. `test-strategy-builder` exige integracao/contrato proporcional ao risco.
6. `plan-quality-checker` passa antes de executar.
7. Execute tarefas atomicas por `workflow-runner` e `task-runner`.
8. Rode spec compliance e code quality; inclua rubric/API reviewer no gate.
9. Registre evidencia por contrato e criterio.
10. Use goal coverage, runtime/release gates e fluxo Git/PR do kernel.

## Saidas
- Contratos afetados.
- Plano de compatibilidade ou migracao.
- Mudancas por fase.
- Testes de contrato.
- Reviews, evidencia, riscos e comunicacao necessaria.
