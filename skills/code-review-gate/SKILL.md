---
name: code-review-gate
description: Use para escolher review integrado ou separado e profundidade proporcional ao modo e ao risco comprovado.
---

# Code Review Gate

## Objetivo
Transformar code review em gate proporcional, sem duplicar reviewers em
`fast`/`standard` nem bloquear por cenarios especulativos.

## Quando usar
- Depois de implementar feature, bugfix, refatoracao ou mudanca de agente.
- Antes de declarar pronto, abrir PR, fazer merge, release ou handoff.
- Quando ha duvida se `diff-reviewer` simples basta.
- Em `critical`, antes dos reviews independentes.

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
1. Receba `mode`, objetivo, diff, arquivos, testes e riscos conhecidos.
2. Retorne:
   - `fast`: `review_mode: integrated`, `depth: light`;
   - `standard`: `review_mode: integrated`, `depth: normal`;
   - `critical`: `review_mode: split`, `depth: deep`.
3. Defina `blocking_threshold: BLOCKER`.
4. Em `fast`/`standard`, faca uma unica revisao de objetivo + qualidade + testes
   + escopo. Nao chame automaticamente os dois reviewers independentes.
5. Em `critical`, roteie `spec-compliance-reviewer` e depois
   `code-quality-reviewer`, com auditors especializados quando o risco exigir.
6. Antes de fechar, cheque o diff contra a tabela de gatilhos de
   `workflows/security-review.md`. Gatilho presente torna o auditor de seguranca
   obrigatorio em qualquer modo, inclusive `fast`, e sua ausencia mantem o gate
   aberto. Isso nao eleva o modo, apenas acrescenta o auditor.
7. Classifique findings como `BLOCKER`, `IMPORTANT`, `NOTE` ou `SPECULATIVE`.
   `BLOCKER` exige reachability, likelihood, impact, supporting evidence e base
   material (requisito, seguranca, dados, regressao, operacao ou aceite).
8. Correcao localizada reabre apenas novo diff, criterios afetados e regressoes
   relacionadas.
9. Aplique o budget de verificacao; sem risco concreto restante, pare passes
   especulativos e registre notas nao bloqueantes.

## Saida obrigatoria
```yaml
review_mode: integrated | split
depth: light | normal | deep
blocking_threshold: BLOCKER
```

Preencha o template somente quando o modo/entrega justificar artefato.

## Criterios de aceite
- Toda mudanca recebe ao menos self-review e diff inspection.
- Gatilho de seguranca no diff sem auditor correspondente bloqueia o gate.
- `fast`/`standard` nao executam reviews separados por default.
- `critical` preserva spec → qualidade.
- `SPECULATIVE` nunca bloqueia; blocker sem evidencia e reclassificado.

## Arquivos de apoio
- Template: ../../templates/code-review-gate-report.md
- Review geral: ../../skills/diff-reviewer/SKILL.md
- Review de agente: ../../skills/agent-code-reviewer/SKILL.md
- Cobertura: ../../skills/goal-coverage-verifier/SKILL.md
- Spec: ../../skills/spec-compliance-reviewer/SKILL.md
- Qualidade: ../../skills/code-quality-reviewer/SKILL.md

## Exemplos de uso
- Codex: `$code-review-gate Decida o nivel de review antes de declarar pronto.`
- Claude Code: `/code-review-gate Verifique se este diff pode fechar ou precisa review profundo.`
