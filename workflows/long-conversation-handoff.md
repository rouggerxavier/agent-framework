# Long Conversation Handoff Workflow

Use quando uma conversa longa precisa virar contexto limpo para outro agente, modelo ou sessao.

## Sequencia
1. Use `context-compressor` para extrair estado atual.
2. Separe fatos, decisoes, suposicoes e pendencias.
3. Liste arquivos, comandos e resultados relevantes.
4. Inclua riscos, falhas de teste e lacunas.
5. Termine com prompt de retomada.
6. Anexe `project-context-loader` ou `repo-map-builder` se o destino for implementacao.

## Saidas
- Resumo operacional.
- Estado atual e decisoes.
- Artefatos relevantes.
- Validacoes feitas.
- Prompt de retomada.
