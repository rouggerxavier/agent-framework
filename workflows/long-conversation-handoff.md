# Long Conversation Handoff Workflow

Use quando uma conversa longa precisa virar contexto limpo para outro agente, modelo ou sessao.

## Sequencia
1. Leia `STATE.md` e use `framework-next` para confirmar a proxima operacao.
2. Use `context-compressor` para extrair estado atual.
3. Separe fatos, decisoes, suposicoes e pendencias.
4. Liste arquivos, comandos e resultados relevantes.
5. Inclua riscos, falhas de teste e lacunas.
6. Termine com prompt de retomada.
7. Anexe somente trechos relevantes de contexto/spec/decisoes; nao toda a conversa.
8. Use `project-context-loader` se o contexto estiver stale.

## Saidas
- Resumo operacional.
- Estado atual e decisoes.
- Artefatos relevantes.
- Validacoes feitas.
- Prompt de retomada.
- Instrucao para reler `STATE.md` e rodar `framework-next`.
