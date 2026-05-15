# Security Privacy Rubric

Use para revisar codigo, configs e fluxos com dados sensiveis.

## Areas
- Authn e authz.
- Dados pessoais, financeiros ou confidenciais.
- Secrets, tokens, cookies e sessoes.
- Logs, analytics, exports e backups.
- Uploads, arquivos, webhooks e chamadas externas.
- CORS, CSP, headers e storage.

## Checklist
- Permissoes sao checadas no servidor.
- Entradas externas sao validadas e normalizadas.
- Secrets nao aparecem em codigo, logs, erro ou client bundle.
- Dados sensiveis sao minimizados em responses e logs.
- Operacoes criticas tem auditoria ou rastreabilidade.
- Erros nao revelam detalhes internos desnecessarios.

## Severidade
- Critical: vazamento de segredo, bypass de auth ou acesso indevido a dados sensiveis.
- High: permissao excessiva ou validacao ausente em boundary.
- Medium: logging sensivel ou hardening ausente em fluxo importante.
- Low: melhoria defensiva sem explorabilidade clara.
