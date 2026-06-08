---
name: env-gitignore-auditor
description: Use para checar .gitignore, .env.example, secrets, tokens, config local, logs, traces, caches e artefatos gerados em agentes ou repos.
---

# Env Gitignore Auditor

## Objetivo
Evitar vazamento de secrets e sujeira operacional no repo, garantindo `.gitignore`, `.env.example`, docs e configs locais coerentes.

## Quando usar
- Ao criar ou alterar agente/backend que usa env vars, tokens, providers, logs, traces, caches ou artefatos gerados.
- Antes de commit/release que mexe em `.env.example`, `.gitignore`, configs, CI secrets ou runtime logs.
- Quando existe risco de token, chave, arquivo local ou output de agente ser commitado.
- Ao preparar repo para outras pessoas rodarem localmente.

## Quando nao usar
- Para auditoria completa de configs; use `config-surface-auditor`.
- Para seguranca ampla de agente; use `agent-security-auditor`.
- Para rotinas sem arquivos locais, env vars ou artefatos.

## Entradas esperadas
- `.gitignore`, `.env.example`, docs de setup e config files.
- Lista de env vars, providers, tokens e artefatos gerados.
- Logs/traces/caches conhecidos e diretorios temporarios.
- Diff ou status do repo, se houver.

## Workflow
1. Inventarie env vars, secrets esperados, arquivos locais, logs, traces, caches e outputs gerados.
2. Verifique `.env.example`: nomes corretos, placeholders seguros, comentarios minimos e sem valores reais.
3. Verifique `.gitignore`: `.env*` local, logs, traces, caches, temp, credentials, dumps, screenshots sensiveis e build artifacts.
4. Procure risco de secrets no diff, nomes de arquivos, docs, exemplos e logs, sem repetir valores sensiveis na saida.
5. Verifique docs: como configurar localmente, onde obter secrets e quais arquivos nunca commitar.
6. Recomende patch, limpeza, rotacao de secret se necessario e verificacao antes de commit.

## Saida obrigatoria
Preencha `../../templates/env-gitignore-report.md` com inventario, gaps, patches, docs e riscos residuais.

## Criterios de aceite
- Nunca copiar secret real para a resposta; use marcador como `[REDACTED]`.
- `.env.example` deve conter placeholders, nao credenciais.
- `.gitignore` deve cobrir artefatos reais do projeto, nao uma lista aleatoria gigante.
- Se secret possivelmente vazou, recomendar rotacao e investigacao de historico git.

## Arquivos de apoio
- Template: ../../templates/env-gitignore-report.md
- Config: ../../skills/config-surface-auditor/SKILL.md
- Docs: ../../skills/docs-sync-auditor/SKILL.md
- Seguranca: ../../skills/security-privacy-audit/SKILL.md

## Exemplos de uso
- Codex: `$env-gitignore-auditor Revise .gitignore, .env.example e logs antes do commit.`
- Claude Code: `/env-gitignore-auditor Cheque secrets e artefatos locais deste repo.`
