---
name: code-quality-reviewer
description: Use como segundo reviewer independente em critical; em fast/standard qualidade entra na revisao integrada.
---

# Code Quality Reviewer

## Objetivo

Avaliar qualidade proporcionalmente, com segunda etapa independente apenas em
`critical`.

## Quando usar

- Em `critical`, depois de spec compliance `PASS` ou `PASS_WITH_NOTES`.
- Em `fast`/`standard`, como parte do review integrado.
- Novamente depois de correcao que invalide a aprovacao anterior.

## Quando nao usar

- Como reviewer separado em `fast`/`standard` por default.
- Em `critical`, quando o reviewer implementou a tarefa ou antes da conformidade.
- Para aprovar sem inspecionar diff, arquivos, testes e evidencia.

## Entradas esperadas

- Goal, mode, diff, arquivos, testes e riscos.
- Em `critical`, resultado e spec review aprovados.
- Diff, arquivos, testes e evidence ledger.
- Rubrics/reviewers especializados selecionados pelo `code-review-gate`.

## Workflow

1. Em todos os modos, inspecione diff, arquivos e testes diretamente.
2. Em `fast`/`standard`, avalie goal + bugs + padroes + testes + escopo em uma
   unica revisao integrada, sem exigir spec review previa ou template.
3. Em `critical`, confirme spec approval e independencia, use rubrics
   especializadas, preencha template e valide pelo CLI.
4. Para cada finding, demonstre reachability, likelihood, impact e supporting
   evidence antes de marcar `BLOCKER`; caso contrario use `IMPORTANT`, `NOTE` ou
   `SPECULATIVE`.
5. Em correcao localizada, revise somente novo diff e areas afetadas, salvo
   descoberta de risco material.

## Saida obrigatoria

- Classificacao, areas verificadas, diff/testes inspecionados e findings.
- Em `critical`, relatorio formal e skills/rubrics especializadas usadas.

## Criterios de aceite

- Ordem spec → qualidade preservada em `critical`.
- `fast`/`standard` usam uma revisao integrada.
- Mudanca exigida invalida aprovacoes afetadas e volta ao implementador.
- Aprovacao nao afirma que testes rodaram sem evidencia propria.
- `SPECULATIVE` nunca bloqueia.

## Arquivos de apoio

- Review geral: ../../skills/diff-reviewer/SKILL.md
- Gate: ../../skills/code-review-gate/SKILL.md
- Rubric: ../../rubrics/diff-review.md
- Relatorio: ../../templates/code-quality-review.md

## Exemplos de uso

- Codex: `$code-quality-reviewer Revise esta tarefa depois do PASS de spec.`
- Claude Code: `/code-quality-reviewer Faça a segunda etapa do review independente.`
