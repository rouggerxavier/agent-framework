---
name: git-decision-router
description: Use para decidir commit direto, esperar validacao, criar branch, abrir PR, deixar unstaged ou pedir review com base em risco e fase.
---

# Git Decision Router

## Objetivo
Escolher a proxima acao de git sem automatismo perigoso: commit direto, esperar validacao, criar branch, abrir PR, deixar unstaged ou pedir review.

## Quando usar
- Depois de implementar ou revisar uma mudanca.
- Antes de stage, commit, PR, handoff ou release.
- Quando ha duvida entre commit direto e esperar validacao humana/QA/review.
- Em mudancas que tocam agente, tools, runtime, env, auth, dados, security, logs, model routing ou dependencias.

## Quando nao usar
- Antes de haver diff, resumo de mudanca ou objetivo claro.
- Para escrever mensagem de commit detalhada; use `commit-readiness-checker`.
- Para criar PR notes; use `pr-description-builder`.

## Entradas esperadas
- Objetivo da mudanca e diff/status atual.
- Testes, QA, review e gates executados.
- Risco: contrato, dados, auth, secrets, runtime, agente, tools, logs, docs ou dependencia.
- Preferencia do usuario sobre commit/PR, se houver.

## Workflow
1. Classifique escopo: docs trivial, codigo local, contrato, runtime, agente, security, dados ou release.
2. Verifique estado: unstaged/staged, branch, arquivos nao relacionados e gates pendentes.
3. Escolha decisao:
   - `commit direct`: docs/copy/config simples, teste/verificacao suficiente, sem risco de contrato;
   - `wait validation`: agente, tools, runtime, env, auth, dados, security, dependencia ou QA pendente;
   - `create branch`: mudanca multi-arquivo, longa, arriscada ou ainda sem branch dedicada;
   - `open PR`: precisa review, evidencias, rollback ou comunicacao;
   - `leave unstaged`: work in progress, diff misto, risco incerto ou falta de aceite.
4. Se commit for permitido, chamar `commit-readiness-checker`.
5. Se PR for recomendado, chamar `pr-description-builder`.
6. Registre decisao, motivo, bloqueios e proximo comando sugerido sem executar git destrutivo.

## Saida obrigatoria
Preencha `../../templates/git-decision-report.md` com decisao, motivo, gates pendentes, acao recomendada e riscos.

## Criterios de aceite
- Nao recomendar commit direto para mudanca de alto risco sem review/QA proporcional.
- Separar arquivos relacionados de sujeira nao relacionada no working tree.
- Se houver secrets, dados ou env vars, bloquear ate auditoria apropriada.
- Respeitar pedido explicito do usuario sobre nao commitar ou esperar validacao.

## Arquivos de apoio
- Template: ../../templates/git-decision-report.md
- Commit: ../../skills/commit-readiness-checker/SKILL.md
- PR: ../../skills/pr-description-builder/SKILL.md
- Review: ../../skills/code-review-gate/SKILL.md

## Exemplos de uso
- Codex: `$git-decision-router Decida se este diff pode ser commitado agora.`
- Claude Code: `/git-decision-router Escolha commit, PR ou esperar validacao para esta mudanca.`
