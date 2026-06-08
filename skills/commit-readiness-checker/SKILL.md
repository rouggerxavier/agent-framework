---
name: commit-readiness-checker
description: "Use para checar se um commit esta pronto: diff, escopo, testes, docs, secrets, arquivos mistos, mensagem e validacao pendente."
---

# Commit Readiness Checker

## Objetivo
Validar se um commit pode ser feito com seguranca, garantindo escopo coeso, evidencias proporcionais, ausencia de secrets e mensagem clara.

## Quando usar
- Antes de stage/commit quando `git-decision-router` permite commit.
- Quando o working tree tem muitos arquivos, arquivos nao relacionados ou artefatos gerados.
- Antes de commit direto em docs, skill, backend, agente ou config.
- Quando a mensagem de commit precisa refletir escopo e validacao.

## Quando nao usar
- Para decidir se deve commitar; use `git-decision-router`.
- Para revisar codigo em profundidade; use `code-review-gate` ou `diff-reviewer`.
- Para PR completo; use `pr-description-builder`.

## Entradas esperadas
- Diff/status, arquivos pretendidos para commit e objetivo.
- Testes/verificacoes executadas.
- Gaps aceitos, docs alteradas e riscos.
- Mensagem de commit proposta, se houver.

## Workflow
1. Verifique escopo: arquivos pertencem ao mesmo objetivo e nao misturam etapas incompativeis.
2. Verifique seguranca: secrets, tokens, `.env`, logs, dumps, caches e artefatos locais.
3. Verifique evidencias: teste, lint, build, QA, review ou justificativa proporcional ao risco.
4. Verifique docs: README, env example, changelog ou runbook quando comportamento/config mudou.
5. Verifique mensagem: tipo/escopo, resumo claro, sem prometer mais do que o diff faz.
6. Classifique: `ready`, `ready with notes` ou `blocked`.

## Saida obrigatoria
Preencha `../../templates/commit-readiness-report.md` com veredito, arquivos, checks, mensagem sugerida e bloqueios.

## Criterios de aceite
- Commit nao deve misturar trabalho nao relacionado.
- Secrets ou artefatos locais bloqueiam commit.
- Testes ausentes precisam ser justificados para mudanca de baixo risco; alto risco bloqueia.
- Mensagem de commit deve ser curta, concreta e alinhada ao diff.

## Arquivos de apoio
- Template: ../../templates/commit-readiness-report.md
- Git decision: ../../skills/git-decision-router/SKILL.md
- Docs: ../../skills/docs-sync-auditor/SKILL.md
- Security: ../../skills/env-gitignore-auditor/SKILL.md

## Exemplos de uso
- Codex: `$commit-readiness-checker Cheque se posso commitar este diff.`
- Claude Code: `/commit-readiness-checker Valide escopo, testes, secrets e mensagem do commit.`
