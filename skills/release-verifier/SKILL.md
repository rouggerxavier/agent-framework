---
name: release-verifier
description: Use para verificar readiness de release com checklist tecnico, QA, riscos, evidencias, changelog, rollback e decisao go/no-go.
---

# Release Verifier

## Objetivo
Determinar se uma entrega esta pronta para release com evidencias suficientes, riscos conhecidos e decisao clara.

## Quando usar
- Antes de deploy, merge final ou entrega para usuario.
- Quando ha checklist de QA, release notes ou rollback a revisar.
- Depois de feature, bugfix critico ou refatoracao.

## Quando nao usar
- Para planejar implementacao inicial.
- Para substituir QA runtime quando app precisa ser testado.
- Para aprovar release com blocker conhecido.

## Entradas esperadas
- Escopo da release ou diff.
- Ambiente de teste e comandos disponiveis.
- Bugs conhecidos e tolerancia a risco.
- Checklist de produto, QA, seguranca ou operacao.

## Workflow
Siga `../../workflows/release.md`. Especifico desta skill:
1. Confirme escopo, versao e ambiente.
2. Aplique a rubric de testes e a de docs-sync (ver Arquivos de apoio).
3. Classifique blockers/non-blockers e emita go/no-go com evidencias.

## Saida obrigatoria
Preencha `../../templates/release-checklist.md` (decisao go/no-go, checks e
resultados, blockers, riscos aceitos, rollback, itens de release notes).

## Criterios de aceite
- Nao aprovar release com blocker aberto.
- Evidencia executada vs suposicao; comandos/ambientes usados.
- Decisao operacionalmente clara.

## Arquivos de apoio
Nao copie estes checklists na skill; aplique-os a partir daqui.
- Workflow: ../../workflows/release.md
- Rubric: ../../rubrics/testing.md
- Rubric: ../../rubrics/docs-sync.md
- Rubric: ../../rubrics/data-migration.md (se a release inclui migration)
- Template: ../../templates/release-checklist.md

## Exemplos de uso
- Codex: `$release-verifier Verifique se este PR esta pronto para merge.`
- Claude Code: `/release-verifier Monte checklist go/no-go para deploy.`
