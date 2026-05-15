---
name: diff-reviewer
description: Use para revisar diffs ou PRs com foco em bugs, regressao, contratos, seguranca, testes faltantes e padroes locais.
---

# Diff Reviewer

## Objetivo
Revisar mudancas de codigo com foco em risco real: regressao, quebra de contrato, seguranca, dados, edge cases e cobertura.

## Quando usar
- Antes de merge ou release.
- Ao revisar trabalho de outro agente ou humano.
- Quando diff toca codigo compartilhado, API, auth, dados ou UI critica.

## Quando nao usar
- Para explicar codigo inteiro sem diff.
- Para discutir estilo cosmetico antes de riscos funcionais.
- Para aprovar sem evidencia suficiente.

## Entradas esperadas
- Diff, PR, branch ou lista de arquivos alterados.
- Objetivo da mudanca.
- Rubrics relevantes, se houver.

## Workflow
1. Entenda objetivo e escopo real do diff.
2. Aplique a rubric de revisao e a de testes (ver Arquivos de apoio).
3. Separe bloqueadores de melhorias opcionais.
4. Reporte no formato do template de auditoria.

## Saida obrigatoria
Conforme `../../templates/audit-report.md`, com achados priorizados por
severidade antes do resumo.

## Criterios de aceite
- Findings antes do resumo; cada achado com risco concreto e evidencia.
- Nao marcar preferencia pessoal como bug.
- Informe limites da revisao e testes nao executados.
- Demais criterios: rubric em Arquivos de apoio.

## Arquivos de apoio
Nao copie estes checklists na skill; aplique-os a partir daqui.
- Rubric: ../../rubrics/diff-review.md
- Rubric: ../../rubrics/testing.md
- Rubric: ../../rubrics/data-migration.md (se o diff toca migration/dados)
- Template: ../../templates/audit-report.md

## Exemplos de uso
- Codex: `$diff-reviewer Revise o diff atual antes do merge.`
- Claude Code: `/diff-reviewer Audite este PR contra regressao e testes faltantes.`
