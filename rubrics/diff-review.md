# Diff Review Rubric

Use para revisar PRs, patches e trabalho de agentes.

## Ordem
1. Objetivo do diff e escopo real.
2. Contratos alterados.
3. Riscos funcionais e regressao.
4. Tratamento de erro, dados e estado.
5. Testes e verificacao.
6. Manutencao e legibilidade.

## Severidade
- Blocker: quebra fluxo critico, perda de dados, falha de seguranca ou build quebrada.
- High: bug provavel em caminho comum ou contrato quebrado.
- Medium: edge case relevante, teste faltante ou manutencao arriscada.
- Low: melhoria local sem risco imediato.

## Checklist
- O diff implementa o objetivo sem trabalho lateral excessivo.
- Caminhos de erro e entradas invalidas foram considerados.
- Compatibilidade com consumidores existentes foi preservada.
- Testes cobrem comportamento novo e regressao principal.
- Docs, config e env foram atualizados quando necessario.
