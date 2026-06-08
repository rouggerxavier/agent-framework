---
name: docs-sync-auditor
description: Use para auditar se README, env vars, API docs, schemas, changelog, runbooks e release notes acompanham mudancas.
---

# Docs Sync Auditor

## Objetivo
Garantir que documentacao operacional e tecnica acompanha mudancas de codigo, API, configs, dados ou release, sem criar docs desnecessarias.

## Quando usar
- Depois de mudanca em API, env vars, comandos, migrations, auth, deploy ou integracoes.
- Antes de release, PR ou handoff quando docs podem ficar defasadas.
- Ao revisar diff com README, schemas, exemplos, changelog ou runbooks.
- Quando breaking change precisa de migracao ou aviso.

## Quando nao usar
- Para escrever documentacao longa do zero sem mudanca tecnica; use prompt/refino dedicado.
- Para revisar codigo por bug; use `diff-reviewer`.
- Para aprovar release inteira; use `release-verifier` ou `backend-release-packager`.

## Entradas esperadas
- Diff, resumo da mudanca, plano ou release notes.
- Docs existentes: README, env examples, API docs, schemas, runbooks, changelog.
- Publico afetado: usuario, dev, operador, cliente API ou suporte.

## Workflow
1. Identifique superficies documentais afetadas pela mudanca.
2. Compare comportamento real e docs atuais: comandos, env vars, payloads, erros, migrations e rollback.
3. Classifique atualizacoes:
   - obrigatorias: quebram uso, operacao ou contrato se ausentes;
   - recomendadas: reduzem suporte/retrabalho;
   - desnecessarias: ruido ou duplicacao.
4. Verifique que exemplos nao incluem secrets reais.
5. Aponte docs obsoletas ou conflitantes.
6. Recomende edicoes minimas e riscos se ficarem pendentes.

## Saida obrigatoria
Preencha `../../templates/docs-sync-report.md` com docs afetadas, updates obrigatorios/opcionais, evidencias e riscos.

## Criterios de aceite
- Separar docs obrigatorias de melhorias opcionais.
- Nao propor doc nova quando atualizar uma existente basta.
- Contratos de API e env vars devem refletir comportamento real.
- Breaking changes exigem aviso, migracao ou risco aceito.

## Arquivos de apoio
- Template: ../../templates/docs-sync-report.md
- Rubric: ../../rubrics/docs-sync.md
- API: ../../skills/api-contract-auditor/SKILL.md
- Release: ../../skills/release-verifier/SKILL.md

## Exemplos de uso
- Codex: `$docs-sync-auditor Veja quais docs precisam mudar neste PR.`
- Claude Code: `/docs-sync-auditor Audite README, env vars e API docs para esta release.`
