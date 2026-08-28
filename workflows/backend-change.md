# Backend Change Workflow

Use para mudancas backend sem presumir que backend significa `critical`.

## Fast

- Texto de resposta, configuracao localizada ou endpoint simples seguindo padrao:
  inspect → implement → targeted tests → diff review.

## Standard

- Endpoint/feature moderada, mudanca distribuida ou refatoracao moderada:
  focused grounding → short plan → implement → tests → integrated review.

## Critical

- Auth/autorizacao, migration, pagamento/financeiro, dados destrutivos,
  sincronizacao, contrato externo sensivel ou rollback complexo:
  `framework-next` → spec → plan/seal → contratos → `workflow-runner` →
  task-runner → evidence → split reviews → complete verification.

## Gates

- API simples nao e critica apenas por ser backend.
- Auditors de API, dados e observabilidade entram somente quando houver risco ou
  contrato concreto.
- Auditors de seguranca nao sao discricionarios: valem os gatilhos de
  `workflows/security-review.md`, em qualquer modo.
- Migration exige forward e rollback/recuperacao.
- Integracao externa critica exige testes de contrato e integracao.

## Saidas

- Saidas seguem a matriz do modo; artefatos persistentes completos existem apenas
  em `critical`.
