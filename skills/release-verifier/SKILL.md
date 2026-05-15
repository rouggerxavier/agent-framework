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
1. Confirme escopo, versao e ambiente.
2. Verifique testes automatizados, smoke test e fluxos criticos.
3. Revise migrations, flags, config, observabilidade e rollback.
4. Classifique blockers, non-blockers e riscos aceitos.
5. Emita decisao go/no-go com evidencias.

## Saida obrigatoria
- Decisao go/no-go.
- Checks executados e resultados.
- Blockers e pendencias.
- Riscos aceitos.
- Plano de rollback ou mitigacao.
- Itens para release notes.

## Criterios de aceite
- Nao aprovar release com blocker aberto.
- Diferenciar evidencia executada de suposicao.
- Incluir comandos, ambientes ou artefatos usados.
- A decisao deve ser operacionalmente clara.

## Exemplos de uso
- Codex: `$release-verifier Verifique se este PR esta pronto para merge.`
- Claude Code: `/release-verifier Monte checklist go/no-go para deploy.`
