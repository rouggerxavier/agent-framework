---
name: backend-release-packager
description: Use para empacotar release backend com escopo, evidencias, contratos, migrations, testes, docs, riscos, rollback e PR notes.
---

# Backend Release Packager

## Objetivo
Montar um pacote final de entrega backend que deixe claro o que mudou, como foi verificado, quais riscos existem, como fazer rollback e o que comunicar.

## Quando usar
- Antes de PR, merge, deploy ou handoff de feature backend relevante.
- Depois de `goal-coverage-verifier`, `data-migration-auditor`, `docs-sync-auditor` ou testes finais.
- Quando ha API, jobs, auth, dados, dependencias, migrations ou integracoes externas.
- Para preparar PR description, release notes, rollback e checklist operacional.

## Quando nao usar
- Para planejar implementacao inicial; use `backend-slice-planner`.
- Para aprovar release com blocker aberto; resolva ou declare bloqueado.
- Para mudanca trivial classificada como `fast`.

## Entradas esperadas
- Objetivo, diff/resumo, plano e criterio de aceite.
- Testes/comandos executados e resultados.
- Achados de contrato, dados, dependencia, docs e seguranca, se houver.
- Branch/commit, ambiente e tolerancia a risco.

## Workflow
1. Resuma escopo: in, out e comportamento alterado.
2. Liste contratos backend afetados: API, eventos, jobs, dados, auth e integracoes.
3. Consolide evidencias: testes, comandos, QA, reviews e verificadores.
4. Cheque gates pendentes: migration, docs, dependency, security, performance e rollback.
5. Classifique riscos aceitos e blockers.
6. Monte rollback: tecnico, operacional e comunicacao.
7. Produza texto pronto para PR/release sem esconder lacunas.

## Saida obrigatoria
Preencha `../../templates/backend-release-package.md` com escopo, evidencias, gates, riscos, rollback e PR/release notes.

## Criterios de aceite
- Nao marcar pronto se houver blocker sem decisao.
- Evidencia executada deve ser separada de verificacao recomendada.
- Rollback e comunicacao aparecem quando houver risco operacional.
- O pacote deve permitir review ou deploy sem redescobrir contexto.

## Arquivos de apoio
- Template: ../../templates/backend-release-package.md
- Release: ../../skills/release-verifier/SKILL.md
- Cobertura: ../../skills/goal-coverage-verifier/SKILL.md
- Docs: ../../skills/docs-sync-auditor/SKILL.md
- Dados: ../../skills/data-migration-auditor/SKILL.md

## Exemplos de uso
- Codex: `$backend-release-packager Monte pacote de release para este backend.`
- Claude Code: `/backend-release-packager Gere PR notes, rollback e checklist final desta entrega.`
