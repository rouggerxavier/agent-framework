---
name: dependency-risk-auditor
description: Use para auditar novas dependencias, pacotes e libs quanto a legitimidade, manutencao, licenca, seguranca, lockfile e custo operacional.
---

# Dependency Risk Auditor

## Objetivo
Avaliar se uma dependencia nova ou alterada e necessaria, legitima e segura o bastante para entrar no projeto, especialmente em backend e supply chain.

## Quando usar
- Antes de instalar pacote, SDK, plugin, action, imagem ou lib nova.
- Ao revisar diff com `package.json`, lockfile, requirements, Gemfile, go.mod, Dockerfile ou CI.
- Quando um plano recomenda biblioteca externa.
- Para backend critico, auth, pagamentos, dados, crypto, rede ou build tooling.

## Quando nao usar
- Para dependencia ja consolidada sem mudanca.
- Para escolher arquitetura geral; use `architecture-decision`.
- Para substituir auditoria formal de seguranca quando o risco for alto.

## Entradas esperadas
- Nome, versao e ecossistema da dependencia.
- Motivo de uso e alternativa sem dependencia.
- Diff de manifestos/lockfiles ou plano de instalacao.
- Dados processados e superficie em runtime ou build.

## Workflow
1. Identifique pacote, versao, origem, runtime/build/dev e motivo declarado.
2. Confirme necessidade: problema resolvido, alternativas nativas e custo de remover depois.
3. Audite legitimidade: nome parecido, fonte, mantenedores, repositorio, release recente e sinais de abandono.
4. Audite risco: licenca, CVEs conhecidas se disponivel localmente, scripts de install, permissoes, rede, secrets, transitive deps e lockfile.
5. Classifique decisao:
   - `approve`: risco baixo e necessidade clara;
   - `approve with guardrails`: uso aceitavel com pin, wrapper, teste ou isolamento;
   - `needs human verification`: fonte/risco incerto;
   - `reject`: necessidade fraca ou risco alto.
6. Recomende teste, pin/versionamento, rollback e documentacao minima.

## Saida obrigatoria
Preencha `../../templates/dependency-risk-report.md` com decisao, evidencia, riscos, guardrails, alternativas e verificacao.

## Criterios de aceite
- Nao recomendar instalar pacote suspeito sem verificacao humana.
- Separar risco de runtime, build e dev-only.
- Lockfile e pin/versionamento sao considerados quando aplicavel.
- Se a evidencia externa nao foi verificada, marcar explicitamente como nao verificada.

## Arquivos de apoio
- Template: ../../templates/dependency-risk-report.md
- Seguranca: ../../skills/security-privacy-audit/SKILL.md
- Arquitetura: ../../skills/architecture-decision/SKILL.md
- Release: ../../skills/release-verifier/SKILL.md

## Exemplos de uso
- Codex: `$dependency-risk-auditor Audite esta nova dependencia antes de instalar.`
- Claude Code: `/dependency-risk-auditor Revise lockfile e risco de supply chain deste PR.`
