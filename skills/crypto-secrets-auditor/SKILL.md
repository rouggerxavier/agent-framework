---
name: crypto-secrets-auditor
description: Use para auditar segredos hardcoded, chaves e certificados no codigo, vazamento em log ou bundle, e criptografia fraca (MD5, SHA1, DES, hash sem salt, TLS sem verificacao).
---

# Crypto Secrets Auditor

## Objetivo
Encontrar segredo exposto e primitiva criptografica inadequada, e transformar
cada achado em acao: rotacionar, remover ou migrar algoritmo.

## Quando usar
- Diff que introduz credencial, chave, certificado, token de integracao ou config de auth.
- Codigo que faz hash de senha, cifra dado, assina token, gera identificador de seguranca ou compara segredo.
- Suspeita de segredo em log, erro, telemetria, bundle de frontend ou historico do git.
- Antes de release que toca autenticacao, pagamento ou dado pessoal.

## Quando nao usar
- Apenas higiene de `.gitignore`, `.env.example` e artefatos locais: use `env-gitignore-auditor`.
- Superficie completa de configuracao e defaults: use `config-surface-auditor`.
- Segredo dentro de manifest, IaC ou pipeline: use `infra-security-auditor`.
- Redaction em logs de agente: use `agent-observability-auditor`.

## Entradas esperadas
- Diff ou arvore em escopo, incluindo testes, fixtures, scripts e CI.
- Onde os segredos deveriam vir (env, secret manager, provider).
- Usos criptograficos existentes e o que cada um protege.
- Acesso ao historico do git, se a busca incluir commits anteriores.

## Workflow
1. Varra codigo, testes, fixtures, scripts, CI e docs por credencial literal, chave privada e certificado.
2. Para cada candidato, decida se e real, exemplo ou placeholder; nunca copie o valor para o relatorio.
3. Se o segredo for real, trate como vazado: rotacao primeiro, remocao do historico depois.
4. Cheque exposicao indireta: log, mensagem de erro, telemetria, resposta de API, bundle e token em URL.
5. Liste os usos criptograficos e compare com a tabela da rubric: senha, assinatura, cifra, aleatoriedade, transporte e comparacao.
6. Marque algoritmo fraco, modo sem autenticacao, salt ausente, IV reutilizado, verificacao de TLS desligada e comparacao nao constante.
7. Defina para cada achado a acao, o dono e a verificacao (comando, teste ou confirmacao de rotacao).

## Saida obrigatoria
Preencha `../../templates/security-audit-report.md` com lens `crypto/secrets`,
achados com severidade, acao de rotacao/migracao e verificacao.

## Criterios de aceite
- Relatorio referencia arquivo:linha e tipo do segredo, nunca o valor.
- Segredo real em ambiente ativo e Critical e exige rotacao, nao apenas remocao do codigo.
- Migracao de hash de senha inclui estrategia de rehash no proximo login.
- Cada achado criptografico nomeia o algoritmo substituto concreto.
- Demais criterios: rubric em Arquivos de apoio.

## Arquivos de apoio
Nao copie estes checklists na skill; aplique-os a partir daqui.
- Rubric: ../../rubrics/crypto-secrets.md
- Template: ../../templates/security-audit-report.md
- Workflow: ../../workflows/security-review.md
- Higiene de repo: ../../skills/env-gitignore-auditor/SKILL.md

## Exemplos de uso
- Codex: `$crypto-secrets-auditor Procure chave hardcoded e hash fraco neste servico.`
- Claude Code: `/crypto-secrets-auditor Revise segredos, MD5, TLS e comparacao de token.`
