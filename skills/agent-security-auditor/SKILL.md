---
name: agent-security-auditor
description: Use para auditar agentes contra prompt injection, data exfiltration, unsafe tool use, secret leakage, logs sensiveis e permissao excessiva.
---

# Agent Security Auditor

## Objetivo
Encontrar riscos especificos de agentes, principalmente abuso de prompt, tool use inseguro, vazamento de dados e falhas de permissao.

## Quando usar
- Antes de release de agente com tools, memoria, dados sensiveis, rede, arquivos ou integracoes externas.
- Ao revisar prompt, tool output handling, logs, auth, env vars ou permissao de tool.
- Quando agente consome conteudo nao confiavel de usuario, web, docs, issues, tickets ou arquivos.
- Depois de mudanca em guardrails, model routing, memoria ou tool registry.

## Quando nao usar
- Para revisar apenas `.env` e `.gitignore`; use `env-gitignore-auditor`.
- Para auditoria geral de app sem agente; use `security-privacy-audit`.
- Para contrato de tool sem threat model de agente; use `tool-contract-auditor`.

## Entradas esperadas
- Prompt/system instructions, tool contracts, runtime flow e config.
- Dados sensiveis, usuarios/atores, fontes nao confiaveis e permissoes.
- Logs, memoria/state, env vars e exemplos de input/output.
- Diff ou escopo de release, se houver.

## Workflow
1. Modele atores e superficies: usuario, agente, tools, memoria, provider, logs e sistemas externos.
2. Procure prompt injection: tool output nao confiavel, documentos maliciosos, override de instrucoes e data smuggling.
3. Procure data exfiltration: secrets, tokens, PII, memoria, logs, arquivos locais e respostas do agente.
4. Audite unsafe tool use: permissao excessiva, side effects sem confirmacao, retry perigoso e falta de allowlist.
5. Audite auth/config/logs: env vars, defaults, traces, audit logs, error messages e redaction.
6. Classifique achados por severidade e recomende guardrail, teste e dono.

## Saida obrigatoria
Preencha `../../templates/agent-security-report.md` com threat model, achados, evidencias, mitigacoes e verificacao.

## Criterios de aceite
- Nao afirmar seguranca total; declarar escopo e lacunas.
- Separar risco exploravel de hardening opcional.
- Achado precisa de evidencia tecnica ou caminho de ataque plausivel.
- Mitigacao deve incluir teste, guardrail ou mudanca concreta.

## Arquivos de apoio
- Template: ../../templates/agent-security-report.md
- Seguranca geral: ../../skills/security-privacy-audit/SKILL.md
- Guardrails: ../../skills/agent-guardrails-implementer/SKILL.md
- Config: ../../skills/env-gitignore-auditor/SKILL.md

## Exemplos de uso
- Codex: `$agent-security-auditor Audite este agente contra prompt injection e vazamento.`
- Claude Code: `/agent-security-auditor Revise tools, logs, memoria e permissoes antes do release.`
