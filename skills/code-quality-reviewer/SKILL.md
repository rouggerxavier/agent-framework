---
name: code-quality-reviewer
description: Use depois da conformidade para revisar independentemente bugs, padroes, seguranca, performance, erros, testes, manutencao e compatibilidade.
---

# Code Quality Reviewer

## Objetivo

Executar a segunda etapa de review, reutilizando `diff-reviewer` e rubrics
especializadas para decidir se a tarefa possui qualidade suficiente.

## Quando usar

- Somente depois de spec compliance `PASS` ou `PASS_WITH_NOTES`.
- Quando `code-review-gate` exigir review simple, deep ou cross-area.
- Novamente depois de correcao que invalide a aprovacao anterior.

## Quando nao usar

- Quando o reviewer implementou a tarefa.
- Antes do review de conformidade.
- Para aprovar sem inspecionar diff, arquivos, testes e evidencia.

## Entradas esperadas

- Resultado e spec review aprovados.
- Diff, arquivos, testes e evidence ledger.
- Rubrics/reviewers especializados selecionados pelo `code-review-gate`.

## Workflow

1. Confirme a aprovacao de spec e independencia do reviewer.
2. Use `diff-reviewer` para bugs, legibilidade, padroes, duplicacao, erros,
   testes, manutencao e compatibilidade.
3. Acione rubrics especializadas para seguranca, performance, dados, API,
   observabilidade ou agente conforme o gate.
4. Inspecione diretamente diff, arquivos e evidencia.
5. Classifique `APPROVED`, `APPROVED_WITH_NOTES` ou `CHANGES_REQUIRED`.
6. Preencha `templates/code-quality-review.md` e valide com
   `scripts/framework-next validate-quality-review`.
7. `CHANGES_REQUIRED` registra findings com evidencia e retorna a `executing`;
   aprovacoes devolvem controle ao runner para verificacao.

## Saida obrigatoria

- Classificacao, areas verificadas e arquivos/evidencias inspecionados.
- Findings com severidade, evidencia e correcao exigida.
- Skills/rubrics especializadas usadas.

## Criterios de aceite

- Ordem spec → qualidade preservada.
- Review independente e baseado em inspecao direta.
- Mudanca exigida invalida aprovacoes afetadas e volta ao implementador.
- Aprovacao nao afirma que testes rodaram sem evidencia propria.

## Arquivos de apoio

- Review geral: ../../skills/diff-reviewer/SKILL.md
- Gate: ../../skills/code-review-gate/SKILL.md
- Rubric: ../../rubrics/diff-review.md
- Relatorio: ../../templates/code-quality-review.md

## Exemplos de uso

- Codex: `$code-quality-reviewer Revise esta tarefa depois do PASS de spec.`
- Claude Code: `/code-quality-reviewer Faça a segunda etapa do review independente.`

