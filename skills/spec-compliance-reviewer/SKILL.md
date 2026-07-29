---
name: spec-compliance-reviewer
description: Use para revisar independentemente uma tarefa contra spec, requisitos, decisoes, contrato, escopo e evidencias antes da revisao de qualidade.
---

# Spec Compliance Reviewer

## Objetivo

Provar se a implementacao cumpre cada criterio e permanece dentro do contrato,
inspecionando codigo e evidencia diretamente.

## Quando usar

- Depois de resultado valido `implementation_complete` e self-review.
- Como primeira etapa obrigatoria do review de tarefa.
- Novamente depois de qualquer correcao que invalide a aprovacao anterior.

## Quando nao usar

- Quando o reviewer foi o implementador.
- Com base apenas no resumo ou afirmacoes do executor.
- Para revisar qualidade geral antes de conformidade passar.

## Entradas esperadas

- Contrato, spec, requisitos e decisoes aplicaveis.
- Diff e arquivos implementados.
- Resultado, comandos, evidence ledger e waivers.

## Workflow

1. Confirme independencia e inspecione diff/arquivos diretamente.
2. Mapeie cada criterio para codigo e evidencia valida.
3. Verifique requisitos ausentes, escopo extra e arquivos fora do contrato.
4. Verifique comandos/resultados e qualquer waiver.
5. Classifique `PASS`, `PASS_WITH_NOTES` ou `BLOCKED`.
6. Preencha `templates/spec-compliance-review.md`.
7. Valide com `scripts/framework-next validate-spec-review`.
8. Em blocker, registre evidencia e devolva ao runner para `reviewing → executing`.

## Saida obrigatoria

- Status de cada criterio e evidencia direta.
- Requisitos ausentes, escopo extra e evidencia invalida.
- Waiver revisado, blockers e classificacao.

## Criterios de aceite

- Todo criterio possui status e evidencia.
- Review lista diff, arquivos e evidencia inspecionados.
- Qualquer gap material produz `BLOCKED`.
- Implementador nao revisa o proprio trabalho.

## Arquivos de apoio

- Evidencia: ../../kernel/evidence-policy.md
- Contrato: ../../templates/task-contract.md
- Relatorio: ../../templates/spec-compliance-review.md
- Qualidade: ../../skills/code-quality-reviewer/SKILL.md

## Exemplos de uso

- Codex: `$spec-compliance-reviewer Compare esta implementacao diretamente com o contrato.`
- Claude Code: `/spec-compliance-reviewer Revise criterios, escopo e evidencias.`

