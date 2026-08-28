---
name: infra-security-auditor
description: Use para auditar configuracao insegura e infraestrutura: debug em producao, CORS amplo, portas expostas, Dockerfile como root, imagem base vulneravel, segredo em YAML e IaC/pipeline.
---

# Infra Security Auditor

## Objetivo
Reduzir superficie de ataque na configuracao de runtime, containers, IaC e
pipeline, com correcao verificavel por comando.

## Quando usar
- Diff que toca Dockerfile, compose, manifest k8s, helm, terraform ou workflow de CI.
- Mudanca em settings de ambiente, feature flag operacional, CORS, headers ou porta publicada.
- Antes de expor servico novo, mudar rede ou publicar ambiente.
- Revisao de ambiente onde debug, console ou credencial padrao possa ter ficado ligado.

## Quando nao usar
- Vulnerabilidade no codigo da aplicacao: use `injection-vulnerability-auditor`.
- Regra de permissao por usuario ou papel: use `authn-authz-auditor`.
- Forca criptografica e segredo no codigo da aplicacao: use `crypto-secrets-auditor`.
- Versao e CVE de biblioteca: use `dependency-risk-auditor`.

## Entradas esperadas
- Arquivos de infra e config em escopo, com ambiente correspondente.
- Topologia minima: o que e publico, o que e interno e quem consome.
- Imagens base, versoes e origem.
- Comandos disponiveis para verificar (build, plan, describe, curl).

## Workflow
1. Separe os ambientes afetados; um mesmo arquivo pode ser aceitavel em dev e Critical em producao.
2. Revise config de aplicacao: debug, stack trace, console, hosts permitidos e paginas administrativas.
3. Revise CORS, headers de seguranca e como a origem e decidida; procure `*` combinado com credenciais.
4. Liste portas publicadas e regras de rede; marque banco, cache, fila e painel expostos.
5. Revise containers: usuario, capacidades, montagens, pin da imagem base e segredo em camada ou `ENV`.
6. Revise IaC e manifests: segredo em texto, storage publico, criptografia, retencao e log de auditoria.
7. Revise pipeline: permissao do token, mascaramento de secret, versao fixada de acao e visibilidade de artefato.
8. Para cada achado, escreva a correcao e o comando que confirma o fechamento.

## Saida obrigatoria
Preencha `../../templates/security-audit-report.md` com lens `infra/container`,
achados por ambiente, correcoes e comando de verificacao.

## Criterios de aceite
- Cada achado nomeia arquivo/recurso, ambiente e o que fica acessivel a quem.
- Achado sem ambiente definido nao recebe severidade Critical.
- Correcao inclui verificacao executavel ou observavel, nao apenas descricao.
- Mudanca de rede ou de exposicao vem com rollback declarado.
- Demais criterios: rubric em Arquivos de apoio.

## Arquivos de apoio
Nao copie estes checklists na skill; aplique-os a partir daqui.
- Rubric: ../../rubrics/infra-security.md
- Template: ../../templates/security-audit-report.md
- Workflow: ../../workflows/security-review.md
- Dependencias: ../../skills/dependency-risk-auditor/SKILL.md

## Exemplos de uso
- Codex: `$infra-security-auditor Revise Dockerfile, compose e CORS antes de publicar.`
- Claude Code: `/infra-security-auditor Cheque debug, portas, root no container e segredo em YAML.`
