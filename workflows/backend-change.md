# Backend Change Workflow

Use para features, refatoracoes e correcoes backend com contratos, dados, jobs,
integracoes ou comportamento runtime.

## Sequencia

1. `framework-next` → route → `project-context-loader`.
2. Use `repo-map-builder` e auditors de API/dados/auth/integracao conforme escopo.
3. Discuta incertezas, congele spec e registre decisoes.
4. Use `workflow-planner` com `backend-slice-planner` ou
   `execution-plan-builder`.
5. Gere contratos integrais; associe requisitos, risco, rollback e testes.
6. Use `plan-quality-checker` como gate para `planned`.
7. Escolha branch/worktree proporcional e execute por `workflow-runner`.
8. Cada tarefa passa por `task-runner`, self-review, spec compliance e code quality.
9. Use `commit-readiness-checker` para commit atomico por tarefa.
10. Verifique objetivo, contratos e runtime antes do release/PR.

## Gates

- API, dados, auth, migration, dependencia, seguranca e observabilidade entram
  quando tocados pelo contrato.
- Migration exige forward e rollback/recuperacao.
- Integracao externa exige testes de contrato e integracao.
- Plan revision e scope expansion retornam ao planner.

## Saidas

- Spec/plano/tarefas e estado persistentes.
- Evidencia e reviews por criterio.
- Commits atomicos, verificacao e pacote de release/PR.

