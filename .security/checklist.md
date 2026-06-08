# Security Checklist

Use antes de PR/release quando houver risco real.

- Entrada externa validada.
- Auth/authz no backend, nao so no frontend.
- Usuario/tenant/org nao acessa recurso alheio.
- Secrets nao aparecem em codigo, docs, logs ou `.env` commitado.
- Erros nao vazam stack, tokens, queries ou dados sensiveis.
- Logs ajudam debug sem expor dados sensiveis.
- Dependencia nova foi revisada.
- Teste negativo cobre abuso principal.

Saida curta:

```text
Finding:
Risk:
Fix:
Test:
```
