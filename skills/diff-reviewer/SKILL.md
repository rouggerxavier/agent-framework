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
2. Leia mudancas por risco: contrato, estado, dados, auth, erros e concorrencia.
3. Procure regressao, edge cases e testes ausentes.
4. Classifique achados por severidade.
5. Separe bloqueadores de melhorias opcionais.

## Saida obrigatoria
- Achados priorizados por severidade.
- Evidencia com arquivo/linha quando disponivel.
- Impacto e sugestao de correcao.
- Testes faltantes ou verificacao recomendada.
- Resumo curto se nao houver achados.

## Criterios de aceite
- Findings devem vir antes do resumo.
- Nao marcar preferencia pessoal como bug.
- Cada achado deve explicar risco concreto.
- Informe limites da revisao e testes nao executados.

## Exemplos de uso
- Codex: `$diff-reviewer Revise o diff atual antes do merge.`
- Claude Code: `/diff-reviewer Audite este PR contra regressao e testes faltantes.`
