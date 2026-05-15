# Coding Standards Rubric

Use para revisar implementacoes, refatoracoes e bugfixes.

## Prioridades
- Preserve comportamento existente salvo pedido contrario.
- Siga padroes locais antes de criar novas abstracoes.
- Mantenha escopo pequeno e relacionado ao objetivo.
- Prefira codigo simples, testavel e legivel.

## Checklist
- A mudanca resolve o problema declarado.
- Nomes, estrutura e estilo seguem o repositorio.
- Contratos publicos continuam compativeis ou tem migracao clara.
- Erros sao tratados de forma coerente.
- Estado, concorrencia, cache e efeitos colaterais foram considerados.
- Nao ha secrets, logs sensiveis ou config local vazando.

## Red flags
- Refatoracao grande misturada com bugfix pequeno.
- Mudanca silenciosa de contrato.
- Fallback que esconde erro real.
- Codigo dificil de testar.

## Saida recomendada
- Status: `aprovado`, `aprovado com ressalvas` ou `bloqueado`.
- Achados por severidade.
- Testes ou verificacoes necessarias.
