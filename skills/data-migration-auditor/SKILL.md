---
name: data-migration-auditor
description: Use para auditar migrations, schema, backfills, expand/contract, compatibilidade, locks, rollback e ordem segura de deploy.
---

# Data Migration Auditor

## Objetivo
Encontrar riscos em mudancas de schema ou dados antes de deploy, garantindo compatibilidade, reexecucao segura, rollback e verificacao proporcional ao volume.

## Quando usar
- Ao criar ou revisar migrations, backfills, seeds, constraints, indices ou mudanca de tipo.
- Quando uma feature backend altera persistencia ou contrato de dados.
- Antes de release com mudanca destrutiva, rename/drop, dedupe ou transformacao em lote.
- Quando um plano menciona banco, schema, data model ou rollback.

## Quando nao usar
- Para logica backend sem persistencia.
- Para auditoria geral de API sem mudanca em dados; use `api-contract-auditor`.
- Para estrategia ampla de arquitetura de dados; use `architecture-decision`.

## Entradas esperadas
- Migration, diff, plano ou descricao da mudanca.
- Banco/ORM, volume aproximado, janelas de deploy e ordem codigo/migration.
- Comandos de teste, staging, backup ou rollback.
- Dependencias de consumidores, jobs, caches e replicas.

## Workflow
1. Classifique a mudanca: schema, dados, backfill, indice, constraint, tipo, default ou limpeza.
2. Cheque compatibilidade entre codigo antigo e novo durante deploy.
3. Verifique estrategia expand/contract quando houver rename, drop ou mudanca destrutiva.
4. Avalie backfill: lote, idempotencia, retomada, tempo, lock e observabilidade.
5. Verifique rollback: down migration, backup, ponto de restauracao ou aceite de irreversibilidade.
6. Defina comandos/verificacoes antes, durante e depois do deploy.
7. Emita veredito e blockers antes de melhorias opcionais.

## Saida obrigatoria
Preencha `../../templates/data-migration-report.md` com veredito, riscos, ordem de deploy, rollback, comandos e gaps.

## Criterios de aceite
- Nao aprovar mudanca destrutiva sem plano expand/contract ou aceite explicito.
- Lock, volume e reexecucao aparecem quando aplicavel.
- Rollback real ou irreversibilidade declarada.
- Evidencia separada de suposicao.

## Arquivos de apoio
- Template: ../../templates/data-migration-report.md
- Rubric: ../../rubrics/data-migration.md
- Testes: ../../skills/test-strategy-builder/SKILL.md
- Release: ../../skills/release-verifier/SKILL.md
- Cobertura: ../../skills/goal-coverage-verifier/SKILL.md

## Exemplos de uso
- Codex: `$data-migration-auditor Audite esta migration antes do deploy.`
- Claude Code: `/data-migration-auditor Revise backfill, locks e rollback desta mudanca.`
