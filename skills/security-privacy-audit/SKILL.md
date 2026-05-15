---
name: security-privacy-audit
description: Use para auditar riscos de seguranca e privacidade em codigo, configs, auth, secrets, permissoes, logs, dados sensiveis e integracoes.
---

# Security Privacy Audit

## Objetivo
Identificar riscos praticos de seguranca e privacidade e recomendar mitigacoes proporcionais.

## Quando usar
- Antes de release que toca auth, permissoes, dados pessoais, pagamentos ou integracoes.
- Ao revisar configs, env vars, logs, storage ou chamadas externas.
- Quando ha suspeita de vazamento, bypass ou excesso de permissao.

## Quando nao usar
- Para substituir pentest formal ou revisao legal.
- Para mudancas sem acesso a dados, auth ou superficie externa.
- Para discutir politica abstrata sem artefato tecnico.

## Entradas esperadas
- Diff, arquivo, fluxo ou descricao da feature.
- Dados processados e usuarios afetados.
- Requisitos de privacidade, compliance ou threat model, se houver.

## Workflow
1. Identifique dados sensiveis, atores e superficies externas.
2. Revise authn/authz, entrada, secrets, logs e armazenamento.
3. Procure exposicao indevida, permissao excessiva e falhas de config.
4. Classifique achados por impacto e explorabilidade.
5. Recomende mitigacao minima, teste e monitoramento.

## Saida obrigatoria
Conforme `../../templates/audit-report.md`: escopo, superficies e dados
sensiveis, achados com severidade, evidencia, mitigacoes e verificacoes.

## Criterios de aceite
- Nao afirmar seguranca total; indicar quando exige revisao especializada.
- Separar risco real de hardening opcional.
- Demais criterios: rubric de seguranca/privacidade em Arquivos de apoio.

## Arquivos de apoio
Nao copie estes checklists na skill; aplique-os a partir daqui.
- Rubric: ../../rubrics/security-privacy.md
- Rubric: ../../rubrics/diff-review.md
- Template: ../../templates/audit-report.md

## Exemplos de uso
- Codex: `$security-privacy-audit Audite este fluxo de auth e dados pessoais.`
- Claude Code: `/security-privacy-audit Revise secrets, permissoes e logs deste PR.`
