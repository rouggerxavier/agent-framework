# API Contract Rubric

Use para revisar endpoints, webhooks, SDKs, schemas e eventos.

## Superficies
- Request body, query, path params e headers.
- Response body, status codes e headers.
- Error shape, codes e mensagens.
- Auth, permissao, rate limit e idempotencia.
- Paginacao, ordenacao, filtros e versionamento.

## Compatibilidade
- Mudanca aditiva costuma ser mais segura que remocao ou renomeacao.
- Campo obrigatorio novo pode quebrar clientes.
- Alterar tipo, nullability ou status code pode ser breaking change.
- Error shape tambem e contrato quando clientes dependem dele.

## Checklist
- Schemas e exemplos refletem comportamento real.
- Erros sao previsiveis e documentados.
- Auth e permissao sao validados por caso de uso.
- Operacoes repetiveis tem idempotencia quando necessario.
- Webhooks consideram assinatura, retry e ordenacao.
- Ha versionamento, deprecacao ou migracao se houver quebra.
