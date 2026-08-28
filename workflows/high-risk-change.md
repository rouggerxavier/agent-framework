# Critical Change Workflow

Use para auth, dados persistidos, migrations, secrets, tools, agentes, model
routing, billing, permissao ou mudanca dificil de reverter.

## Sequencia

1. Confirme evidencia concreta e selecione `critical`; entao inicialize/retome
   com `framework-next`.
2. Ground e registre commit, branch, contexto, unknowns e assumptions.
3. Congele spec e decisoes; inclua invariantes, rollback e stop conditions.
4. `workflow-planner` seleciona auditors e contratos pequenos.
5. `plan-quality-checker` bloqueia gates ausentes.
6. Use branch/worktree isolado; paralelismo somente sem arquivos/contratos comuns.
7. Execute uma tarefa por vez com a politica central de testes.
8. Exija self-review, spec compliance e code quality `deep`/`cross-area`.
9. Aplique `workflows/security-review.md`: os auditores disparados pelos
   gatilhos do diff sao obrigatorios aqui e rodam como reviewers independentes
   do executor.
10. Rode reviewers especializados, runtime QA e goal coverage.
11. Use release gate, commit readiness e PR; nao faça integracao direta sem
    evidencia proporcional.

## Gates

- Falha, stale context, conflito ou scope expansion bloqueia.
- Achado de seguranca `Critical`/`High` sem correcao e teste negativo bloqueia
  integracao; segredo real exposto exige rotacao antes do merge.
- Waiver precisa aprovacao e evidencia alternativa.
- Executor, reviewers e verifier possuem autoridades separadas.

## Saidas

- Decisoes e rollback auditaveis.
- Ledger completo, reviews especializados e blockers resolvidos.
- PR/release com risco residual explicito.
