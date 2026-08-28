---
name: authn-authz-auditor
description: Use para auditar autenticacao, tokens/JWT, sessao, CSRF, autorizacao por recurso (BOLA/IDOR), autorizacao por papel e bypass de fluxo de negocio.
---

# Authn Authz Auditor

## Objetivo
Provar quem pode fazer o que sobre qual recurso, e encontrar onde a checagem
falta, roda tarde demais ou depende de dado enviado pelo cliente.

## Quando usar
- Diff que toca login, token, sessao, cookie, middleware de auth, roles ou permissoes.
- Endpoint que recebe `id` de recurso, `tenant`, `owner` ou parametro de escopo.
- Rota administrativa, area interna ou operacao privilegiada nova.
- Fluxo com etapas obrigatorias, dinheiro, saldo, cupom, cota ou limite.
- Mutacao por cookie sem token anti-CSRF.

## Quando nao usar
- Dado do usuario chegando a query, comando ou parser: use `injection-vulnerability-auditor`.
- Forca de hash, cifra ou segredo exposto: use `crypto-secrets-auditor`.
- CORS, headers, portas e IaC: use `infra-security-auditor`.
- Permissao de tool de agente: use `agent-guardrails-implementer` ou `agent-security-auditor`.

## Entradas esperadas
- Rotas em escopo, com metodo, entrada e efeito.
- Modelo de atores: papeis, tenants, dono do recurso e usuario anonimo.
- Mecanismo de sessao/token e onde a decisao de acesso e tomada.
- Invariantes de negocio que o fluxo precisa preservar.

## Workflow
1. Monte a matriz ator x recurso x acao para o escopo; inclua anonimo, outro usuario, outro tenant e papel menor.
2. Para cada rota, localize onde a identidade e resolvida e onde a permissao e decidida; marque rota sem decisao no servidor.
3. Verifique se o recurso e carregado ja filtrado pelo escopo do chamador, nao filtrado depois.
4. Cheque endpoints privilegiados um a um; negacao por padrao vale mais que middleware presumido.
5. Revise sessao e token: geracao, expiracao, rotacao, revogacao, algoritmo e flags de cookie.
6. Revise CSRF em mutacoes por cookie e a interacao com CORS com credenciais.
7. Teste a ordem do fluxo: pular etapa, repetir etapa, valores vindos do cliente e concorrencia.
8. Registre cada achado como requisicao concreta do atacante e defina o teste negativo.

## Saida obrigatoria
Preencha `../../templates/security-audit-report.md` com lens `access control`,
matriz de atores, achados com severidade e evidencia, correcoes e testes.

## Criterios de aceite
- Cada achado nomeia atacante, vitima, recurso e requisicao que demonstra o acesso indevido.
- Nenhuma rota do escopo fica sem veredito: protegida, exposta ou fora de escopo declarado.
- Correcao acontece no servidor; esconder na UI nao encerra achado.
- Todo achado Critical/High recebe teste negativo especificado.
- Demais criterios: rubric em Arquivos de apoio.

## Arquivos de apoio
Nao copie estes checklists na skill; aplique-os a partir daqui.
- Rubric: ../../rubrics/access-control.md
- Template: ../../templates/security-audit-report.md
- Workflow: ../../workflows/security-review.md
- Injecao: ../../skills/injection-vulnerability-auditor/SKILL.md

## Exemplos de uso
- Codex: `$authn-authz-auditor Cheque IDOR e papel admin nestes endpoints.`
- Claude Code: `/authn-authz-auditor Revise JWT, sessao, CSRF e ordem do checkout.`
