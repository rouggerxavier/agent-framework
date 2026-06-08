---
name: code-review-gate
description: Use para decidir profundidade obrigatoria de code review e bloquear conclusao quando diff toca agentes, auth, secrets, tools, dados ou runtime.
---

# Code Review Gate

## Objetivo
Transformar code review em gate proporcional ao risco, decidindo quando basta review simples, quando precisa review profundo e quando a entrega deve ficar bloqueada.

## Quando usar
- Depois de implementar feature, bugfix, refatoracao ou mudanca de agente.
- Antes de declarar pronto, abrir PR, fazer merge, release ou handoff.
- Quando o diff toca agente, prompt, tools, model routing, runtime behavior, auth, secrets, dados, logs, env vars ou integracoes.
- Quando ha duvida se `diff-reviewer` simples basta.

## Quando nao usar
- Antes de existir diff ou resumo de mudanca.
- Para revisar codigo linha a linha; este gate escolhe a revisao, nao substitui o reviewer.
- Para tarefa trivial de docs/copy sem risco operacional.

## Entradas esperadas
- Objetivo original, diff ou lista de arquivos alterados.
- Testes/QA executados e resultados.
- Areas tocadas: agente, API, dados, auth, env, tools, logs, runtime, docs.
- Riscos conhecidos, plano ou criterios de aceite.

## Workflow
1. Classifique escopo e risco do diff.
2. Escolha review:
   - `none`: docs/copy trivial, sem contrato ou runtime;
   - `simple`: mudanca pequena, baixo risco, testes claros;
   - `deep`: agente, auth, dados, tools, env, security, runtime behavior, model routing ou integracao;
   - `cross-area`: mais de uma area critica ou mudanca dificil de reverter.
3. Verifique precondicoes: testes proporcionais, runtime QA, logs, docs, security/env checks e goal coverage quando aplicavel.
4. Se faltar gate essencial, marque `blocked`.
5. Indique reviewer recomendado: `diff-reviewer`, `agent-code-reviewer`, `security-privacy-audit`, `api-contract-auditor` ou outro asset.
6. Registre decisao e proximo passo minimo para liberar.

## Saida obrigatoria
Preencha `../../templates/code-review-gate-report.md` com decisao, nivel de review, bloqueios, reviewer e evidencias.

## Criterios de aceite
- Nao permitir concluir mudanca de alto risco sem review.
- Review profundo e obrigatorio para agente, tools, auth, secrets, dados, model routing ou runtime behavior.
- Tarefa trivial pode passar sem burocracia, com justificativa curta.
- Todo bloqueio deve apontar gate faltante e acao minima.

## Arquivos de apoio
- Template: ../../templates/code-review-gate-report.md
- Review geral: ../../skills/diff-reviewer/SKILL.md
- Review de agente: ../../skills/agent-code-reviewer/SKILL.md
- Cobertura: ../../skills/goal-coverage-verifier/SKILL.md

## Exemplos de uso
- Codex: `$code-review-gate Decida o nivel de review antes de declarar pronto.`
- Claude Code: `/code-review-gate Verifique se este diff pode fechar ou precisa review profundo.`
