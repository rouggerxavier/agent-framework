---
name: pr-description-builder
description: Use para gerar descricao de PR com escopo, evidencias, riscos, rollback, docs, screenshots/logs e checklist de review quando aplicavel.
---

# PR Description Builder

## Objetivo
Montar uma descricao de PR que permita revisar sem redescobrir contexto: o que mudou, por que, evidencias, riscos, rollback e pontos de atencao.

## Quando usar
- Antes de abrir PR ou enviar handoff para review.
- Quando a mudanca tem risco, multiplos arquivos, agente, backend, API, dados, env, security, logs ou runtime behavior.
- Depois de `code-review-gate`, `goal-coverage-verifier`, QA ou release package.
- Quando reviewers precisam de checklist claro.

## Quando nao usar
- Para commit local simples sem PR.
- Para release package completo de backend; use `backend-release-packager`.
- Para esconder gaps; lacunas devem aparecer como risco ou bloqueio.

## Entradas esperadas
- Objetivo, diff/resumo, arquivos principais e decisao de review.
- Testes/QA/reviews executados e resultados.
- Riscos, rollback, docs, logs/screenshots e pontos pendentes.
- Publico do PR: backend, agente, produto, infra ou docs.

## Workflow
1. Resuma escopo: problema, solucao e fora de escopo.
2. Liste mudancas principais por area.
3. Consolide evidencias executadas: comandos, QA, review, logs/screenshots e verificadores.
4. Liste riscos, mitigacoes, rollback e pontos que reviewer deve olhar.
5. Inclua docs/config/env/migration quando aplicavel.
6. Gere descricao pronta, honesta sobre gaps e sem dados sensiveis.

## Saida obrigatoria
Preencha `../../templates/pr-description.md` com summary, changes, evidence, risks, rollback e checklist.

## Criterios de aceite
- Separar evidencia executada de verificacao recomendada.
- Nao omitir blocker, teste ausente ou risco aceito.
- Descricao deve ser curta o bastante para reviewer usar, mas completa para contexto.
- Logs/screenshots devem ser referenciados sem expor secrets ou dados sensiveis.

## Arquivos de apoio
- Template: ../../templates/pr-description.md
- Release backend: ../../skills/backend-release-packager/SKILL.md
- Review gate: ../../skills/code-review-gate/SKILL.md
- Coverage: ../../skills/goal-coverage-verifier/SKILL.md

## Exemplos de uso
- Codex: `$pr-description-builder Gere uma descricao de PR para esta entrega.`
- Claude Code: `/pr-description-builder Monte PR notes com evidencias, riscos e rollback.`
