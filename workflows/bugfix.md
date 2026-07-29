# Bugfix Workflow

Use para corrigir bugs com reproducao, estado persistente, regressao primeiro e
evidencia.

## Sequencia
1. Use `framework-next` e `project-context-loader`.
2. Route e abra uma fase de bugfix; use `bug-repro-lab`.
3. Reproduza e registre esperado, obtido, comando e evidencia.
4. Se a investigacao for longa, crie blocker e use `persistent-debug-session`.
5. Congele a spec minima: causa observada, comportamento esperado e nao escopo.
6. Use `workflow-planner` para um contrato pequeno com `change_type: bugfix`.
7. `plan-quality-checker` valida contrato, rollback e criterio de regressao.
8. `workflow-runner` seleciona a tarefa e `task-runner` le `read_first`.
9. Crie o teste de regressao e confirme RED pelo motivo esperado.
10. Aplique o fix minimo, confirme GREEN, refatore e rode novamente.
11. Registre comandos, falhas, aceite e self-review.
12. Rode `spec-compliance-reviewer` e depois `code-quality-reviewer`.
13. Correcao retorna a RED/GREEN conforme impacto e repete o review bloqueado.
14. Use `commit-readiness-checker` para commit atomico.
15. `goal-coverage-verifier` confirma ausencia de regressao; finalize por
    `git-decision-router` ou handoff.

## Saidas
- Reproducao e causa com evidencia.
- Fix aplicado ou recomendado.
- Teste de regressao com RED/GREEN/refactor ou waiver valido.
- Self-review, dois reviews independentes e commit por tarefa.
- Estado, comandos, evidencia, riscos e proxima operacao.
