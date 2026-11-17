---
{
  "category": "infra",
  "keywords": [
    "deploy",
    "release",
    "ci\\b",
    "migration",
    "migrac",
    "env\\b",
    "config",
    "dependencia",
    "logs?\\b",
    "performance",
    "docker"
  ],
  "required": []
}
---

# Infraestrutura e operacao

Instrucao: escolha pela parte da infra tocada. Perfil de CI e eixo separado do
modo (ver "Saida obrigatoria"). Nao crie infra nova para necessidade futura.

| Parte | Situacao | Skill | Apoio |
|---|---|---|---|
| Dados | Auditar migration/dados | data-migration-auditor | templates/data-migration-report, rubrics/data-migration |
| Config | Auditar configs/env | config-surface-auditor | templates/config-surface-report, docs-sync-auditor |
| Config | Auditar env/gitignore/secrets | env-gitignore-auditor | templates/env-gitignore-report, config-surface-auditor |
| Dependencias | Auditar dependencia | dependency-risk-auditor | templates/dependency-risk-report, architecture-decision |
| CI | Escolher perfil de CI e politica de espera | ci-throughput-controller | kernel/ci-throughput-policy, templates/ci-throughput-decision |
| CI | Agrupar PRs para CI de integracao | integration-batch-manager | workflows/integration-batch, kernel/ci-throughput-policy |
| Release | Release | release-verifier | workflows/release, templates/release-checklist |
| Release | Empacotar release backend | backend-release-packager | templates/backend-release-package, goal-coverage-verifier |
| Deploy de agente | Implantar e operar agente em nuvem | agent-cloud-deployer | templates/agent-cloud-deploy-spec, infra-security-auditor |
| Logs | Planejar logs de feature | feature-logging-planner | templates/feature-logging-plan, security-privacy-audit |
| Performance | Auditar performance budget | performance-budget-auditor | templates/performance-budget-report, rubrics/performance-budget |
