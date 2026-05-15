---
name: bug-repro-lab
description: Use para investigar bugs com reproducao, hipoteses, evidencia, causa provavel, correcao minima e verificacao de regressao.
---

# Bug Repro Lab

## Objetivo
Transformar um sintoma em bug reproduzivel, causa provavel e correcao minima validada.

## Quando usar
- Para bug report, stack trace, teste falhando ou comportamento inesperado.
- Antes de corrigir area pouco conhecida.
- Quando a reproducao ainda nao esta clara.

## Quando nao usar
- Para feature nova sem comportamento esperado.
- Para ajuste visual simples sem bug reproduzivel.
- Para mudanca ampla sem escopo de bug.

## Entradas esperadas
- Sintoma, erro, teste falhando ou passos conhecidos.
- Ambiente e comandos disponiveis.
- Escopo permitido para investigacao e correcao.

## Workflow
Siga `../../workflows/bugfix.md` de ponta a ponta. Especifico desta skill:
1. Registre esperado, obtido, ambiente e passos conhecidos.
2. Reproduza ou documente por que nao foi possivel reproduzir.
3. Aplique fix minimo e valide regressao pela rubric de testes.

## Saida obrigatoria
- Passos de reproducao ou tentativa; esperado vs obtido.
- Causa provavel com evidencia; mudanca aplicada ou recomendada.
- Verificacao e riscos restantes (formato `../../templates/audit-report.md`).

## Criterios de aceite
- Nao corrigir por palpite quando houver caminho de reproducao.
- Bug nao reproduzido sai como hipotese; fix pequeno e alinhado.
- Regressao conforme rubric de testes em Arquivos de apoio.

## Arquivos de apoio
Nao copie estes checklists na skill; aplique-os a partir daqui.
- Workflow: ../../workflows/bugfix.md
- Rubric: ../../rubrics/testing.md
- Rubric: ../../rubrics/diff-review.md
- Template: ../../templates/audit-report.md

## Exemplos de uso
- Codex: `$bug-repro-lab Reproduza e corrija o erro no checkout.`
- Claude Code: `/bug-repro-lab Investigue este stack trace e proponha fix minimo.`
