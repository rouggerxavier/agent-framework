---
name: config-surface-auditor
description: "Use para revisar superficie de configuracao: env vars, defaults, overrides, secrets, .env.example, .gitignore, logs e artefatos locais."
---

# Config Surface Auditor

## Objetivo
Garantir que configuracao de agente ou backend esteja clara, segura, portavel e verificavel, sem secrets no repo nem defaults perigosos.

## Quando usar
- Ao adicionar ou mudar env vars, provider config, flags, URLs, paths, tokens ou runtime settings.
- Antes de release que depende de `.env`, `.env.example`, `.gitignore`, CI secrets ou config local.
- Ao refatorar agente para remover hardcode e expor configs.
- Quando logs, caches, traces ou artefatos gerados podem vazar dados.

## Quando nao usar
- Para auditoria de seguranca completa; use `security-privacy-audit`.
- Para escolher modelo/provider; use `model-flexibility-auditor`.
- Para config trivial sem secret, ambiente ou comportamento runtime.

## Entradas esperadas
- Diff de configs, env docs, `.gitignore`, runtime files e manifests.
- Lista de env vars esperadas e valores default permitidos.
- Ambientes afetados: local, test, CI, staging, prod.
- Dados sensiveis, logs e artefatos que podem ser gerados.

## Workflow
1. Inventarie env vars, config files, defaults, overrides, secrets, paths, generated files e logs.
2. Verifique fonte de verdade: onde cada config e declarada, documentada, validada e consumida.
3. Audite defaults: nenhum secret real, URL prod perigosa, permissao ampla ou comportamento inseguro por omissao.
4. Audite `.env.example`, docs, `.gitignore`, CI secrets, local overrides e arquivos gerados.
5. Classifique status:
   - `ok`: clara, segura e documentada;
   - `needs docs`: falta exemplo, README ou runbook;
   - `needs validation`: falta runtime validation ou schema;
   - `unsafe`: secret, permissao, log ou default perigoso.
6. Recomende patch minimo, validacao runtime e docs necessarias.

## Saida obrigatoria
Preencha `../../templates/config-surface-report.md` com inventario, gaps, riscos, patches recomendados e verificacao.

## Criterios de aceite
- Secrets reais nunca devem ser copiados para a saida.
- `.env.example` deve conter nomes e placeholders, nao valores sensiveis.
- `.gitignore` deve cobrir env local, logs, caches, traces e artefatos gerados relevantes.
- Config usada em runtime deve ter validacao, default seguro ou erro claro.

## Arquivos de apoio
- Template: ../../templates/config-surface-report.md
- Seguranca: ../../skills/security-privacy-audit/SKILL.md
- Docs: ../../skills/docs-sync-auditor/SKILL.md
- Dependencias: ../../skills/dependency-risk-auditor/SKILL.md

## Exemplos de uso
- Codex: `$config-surface-auditor Revise env vars, .env.example e .gitignore deste agente.`
- Claude Code: `/config-surface-auditor Audite configs e defaults antes do release.`
