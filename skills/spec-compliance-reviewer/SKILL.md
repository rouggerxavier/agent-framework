---
name: spec-compliance-reviewer
description: Use como reviewer independente em critical; em fast/standard a conformidade faz parte do review integrado.
---

# Spec Compliance Reviewer

## Objetivo

Verificar conformidade de modo proporcional, com review independente formal
somente em `critical`.

## Quando usar

- Em `critical`, depois de resultado valido `implementation_complete`.
- Em `fast`/`standard`, como dimensao da revisao integrada, sem novo reviewer.
- Novamente depois de qualquer correcao que invalide a aprovacao anterior.

## Quando nao usar

- Como reviewer separado em `fast`/`standard` por default.
- Em `critical`, quando o reviewer foi o implementador.
- Com base apenas no resumo ou afirmacoes do executor.
- Para revisar qualidade geral antes de conformidade passar.

## Entradas esperadas

- Goal, mode e comportamento esperado.
- Em `critical`: contrato, spec, requisitos e decisoes.
- Diff e arquivos implementados.
- Testes/resultados, riscos e, em `critical`, ledger/waivers.

## Workflow

1. Receba o pacote minimo: goal, mode, diff, files_changed, tests_run,
   acceptance/expected behavior e known_risks.
2. Em `fast`/`standard`, avalie criterios, escopo e testes dentro do review
   integrado; nao exija contrato, ledger, template ou independencia.
3. Em `critical`, confirme independencia, mapeie cada criterio para codigo e
   evidencia, verifique contrato/waivers, preencha template e valide pelo CLI.
4. Classifique findings em `BLOCKER`, `IMPORTANT`, `NOTE`, `SPECULATIVE`;
   `SPECULATIVE` nunca bloqueia.
5. Depois de correcao localizada, reavalie apenas diff/criterios afetados.

## Saida obrigatoria

- `fast`/`standard`: conclusao integrada concisa.
- `critical`: status por criterio, evidencia, escopo, waivers e classificacao.

## Criterios de aceite

- Todo criterio possui status e evidencia.
- Review lista diff, arquivos e evidencia inspecionados.
- Somente gap material e provado produz `BLOCKED`.
- Independencia e obrigatoria apenas no review formal `critical`.

## Arquivos de apoio

- Evidencia: ../../kernel/evidence-policy.md
- Contrato: ../../templates/task-contract.md
- Relatorio: ../../templates/spec-compliance-review.md
- Qualidade: ../../skills/code-quality-reviewer/SKILL.md

## Exemplos de uso

- Codex: `$spec-compliance-reviewer Compare esta implementacao diretamente com o contrato.`
- Claude Code: `/spec-compliance-reviewer Revise criterios, escopo e evidencias.`
