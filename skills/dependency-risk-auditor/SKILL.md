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
- Ao checar componentes ja instalados: versao desatualizada, CVE conhecida, release EOL ou imagem base sem patch.
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
4. Audite risco: licenca, scripts de install, permissoes, rede, secrets, transitive deps e lockfile.
5. Cheque componente vulneravel com a ferramenta nativa do ecossistema (`npm audit`, `pip-audit`, `bundle audit`, `govulncheck`, `cargo audit`, scanner de imagem). Se a ferramenta nao existir no ambiente, registre a lacuna em vez de presumir ausencia de CVE.
6. Para cada CVE encontrada, decida: versao corrigida disponivel, mitigacao temporaria ou aceite com dono e prazo; marque como nao verificado quando faltar dado.
7. Classifique decisao:
   - `approve`: risco baixo e necessidade clara;
   - `approve with guardrails`: uso aceitavel com pin, wrapper, teste ou isolamento;
   - `needs human verification`: fonte/risco incerto;
   - `reject`: necessidade fraca ou risco alto.
8. Recomende teste, pin/versionamento, rollback e documentacao minima.

## Saida obrigatoria
Preencha `../../templates/dependency-risk-report.md` com decisao, evidencia, riscos, guardrails, alternativas e verificacao.

## Criterios de aceite
- Nao recomendar instalar pacote suspeito sem verificacao humana.
- Separar risco de runtime, build e dev-only.
- Lockfile e pin/versionamento sao considerados quando aplicavel.
- Se a evidencia externa nao foi verificada, marcar explicitamente como nao verificada.
- Ausencia de scanner disponivel e registrada como lacuna, nunca como "sem CVE".
- CVE em runtime com correcao disponivel e blocker ate upgrade ou mitigacao com dono.

## Arquivos de apoio
- Template: ../../templates/dependency-risk-report.md
- Seguranca: ../../skills/security-privacy-audit/SKILL.md
- Workflow: ../../workflows/security-review.md
- Infra/imagem base: ../../skills/infra-security-auditor/SKILL.md
- Arquitetura: ../../skills/architecture-decision/SKILL.md
- Release: ../../skills/release-verifier/SKILL.md

## Exemplos de uso
- Codex: `$dependency-risk-auditor Audite esta nova dependencia antes de instalar.`
- Claude Code: `/dependency-risk-auditor Revise lockfile e risco de supply chain deste PR.`
