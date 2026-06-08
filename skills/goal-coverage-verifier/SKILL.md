---
name: goal-coverage-verifier
description: Use para verificar depois da implementacao se objetivo, decisoes, contratos, testes e riscos foram realmente cobertos.
---

# Goal Coverage Verifier

## Objetivo
Verificar de tras para frente se o trabalho implementado cobre o objetivo original, as decisoes tomadas, os contratos afetados e os riscos principais.

## Quando usar
- Depois de implementar feature, bugfix, refatoracao backend, migration ou integracao.
- Antes de release, PR ou handoff quando o risco nao cabe so em "testes passaram".
- Quando ha plano, aceite, diff ou resumo de execucao para comparar.
- Ao fechar gaps depois de QA, review ou verificacao falha.

## Quando nao usar
- Para planejar antes da execucao; use `backend-slice-planner`.
- Para revisar bugs de codigo linha a linha; use `diff-reviewer`.
- Para smoke test runtime de app executavel; use `runtime-qa-audit`.

## Entradas esperadas
- Objetivo original, plano ou criterios de aceite.
- Diff, lista de arquivos alterados ou resumo de execucao.
- Comandos/testes executados e resultados.
- Contratos, decisoes e riscos declarados.

## Workflow
1. Extraia must-haves do objetivo, plano e decisoes.
2. Mapeie cada must-have para evidencia: arquivo, teste, comando, comportamento ou ausencia de evidencia.
3. Verifique contratos backend: API, eventos, schemas, jobs, dados, auth e integracoes.
4. Compare testes executados com riscos principais; marque lacunas sem inventar cobertura.
5. Classifique gaps:
   - `blocker`: objetivo ou contrato critico nao coberto;
   - `high`: risco comum sem teste/evidencia;
   - `medium`: edge relevante, doc ou rollback faltante;
   - `low`: melhoria local ou evidencia desejavel.
6. Recomende fix, teste adicional, aceite de risco ou release bloqueado.

## Saida obrigatoria
Preencha `../../templates/goal-coverage-report.md` com matriz must-have -> evidencia, gaps, testes, riscos aceitos e decisao.

## Criterios de aceite
- Separar evidencia real de inferencia.
- Nao declarar cobertura por teste que nao foi executado.
- Todo gap tem proximo passo ou aceite de risco explicito.
- A decisao final e operacional: `pass`, `pass com ressalvas` ou `bloqueado`.

## Arquivos de apoio
- Template: ../../templates/goal-coverage-report.md
- Revisao: ../../skills/diff-reviewer/SKILL.md
- Testes: ../../skills/test-strategy-builder/SKILL.md
- Release: ../../skills/release-verifier/SKILL.md
- API: ../../skills/api-contract-auditor/SKILL.md

## Exemplos de uso
- Codex: `$goal-coverage-verifier Verifique se este diff cobre o objetivo e os contratos.`
- Claude Code: `/goal-coverage-verifier Compare implementacao, plano e testes antes do PR.`
