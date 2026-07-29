---
name: goal-coverage-verifier
description: Use para verificar cobertura do objetivo diretamente no diff em fast, de forma integrada em standard ou formalmente em critical.
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
1. Confirme o modo e extraia must-haves do objetivo.
2. Em `fast`, compare diretamente objetivo, diff, comportamento esperado e teste
   direcionado; nao crie relatorio formal por default.
3. Em `standard`, faca a revisao integrada de goal + qualidade + testes + escopo.
4. Em `critical`, extraia must-haves de spec/plano/decisoes e mapeie cada um para
   evidence ledger.
5. Em todos os modos, separe evidencia real de inferencia e classifique gaps como
   `BLOCKER`, `IMPORTANT`, `NOTE` ou `SPECULATIVE`.
6. `BLOCKER` exige reachability, likelihood, impact, supporting evidence e base
   material. `SPECULATIVE` nunca bloqueia.
7. Em `critical`, confira reviews separados, waivers, commit/contexto e autorize
   `verifying → ready_to_ship` somente com guards completos.
8. Em `fast`/`standard`, conclua quando criterios importantes e verificacao
   proporcional estiverem atendidos.

## Saida obrigatoria
- `fast`: conclusao direta baseada em diff/teste.
- `standard`: review integrado.
- `critical`: preencha `../../templates/goal-coverage-report.md` e ledger.

## Criterios de aceite
- Separar evidencia real de inferencia.
- Nao declarar cobertura por teste que nao foi executado.
- Todo gap tem proximo passo ou aceite de risco explicito.
- A decisao final e operacional: `pass`, `pass com ressalvas` ou `bloqueado`.
- Somente no lifecycle `critical` o verifier promove `ready_to_ship`.
- O overhead respeita o verification budget do modo.

## Arquivos de apoio
- Template: ../../templates/goal-coverage-report.md
- Revisao: ../../skills/diff-reviewer/SKILL.md
- Testes: ../../skills/test-strategy-builder/SKILL.md
- Release: ../../skills/release-verifier/SKILL.md
- API: ../../skills/api-contract-auditor/SKILL.md

## Exemplos de uso
- Codex: `$goal-coverage-verifier Verifique se este diff cobre o objetivo e os contratos.`
- Claude Code: `/goal-coverage-verifier Compare implementacao, plano e testes antes do PR.`
