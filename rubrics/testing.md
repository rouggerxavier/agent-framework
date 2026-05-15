# Testing Rubric

Use para escolher cobertura proporcional ao risco.

## Risco
- Baixo: copy, docs, estilo sem comportamento.
- Medio: fluxo local, componente isolado, parser simples, validacao.
- Alto: auth, billing, dados persistidos, API publica, migrations, permissao, checkout.

## Tipos
- Unit: regra pura, parser, validacao, formatacao, edge case isolado.
- Integration: contrato entre modulos, banco, API interna, estado compartilhado.
- E2E: fluxo critico de usuario ou integracao de varias camadas.
- Manual QA: estados visuais, acessibilidade, copy e device real.

## Checklist
- O teste cobre requisito ou bug principal.
- Ha caso de erro ou edge case relevante.
- Mudancas em contrato tem teste de compatibilidade.
- UI cobre loading, empty e error state quando aplicavel.
- Comandos de teste sao registrados.
- Lacunas sao declaradas.

## Red flags
- Apenas happy path em fluxo critico.
- Snapshot substituindo assercao relevante.
- Teste que replica implementacao.
- Teste instavel por tempo, rede ou dados.
