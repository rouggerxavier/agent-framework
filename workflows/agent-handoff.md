# Agent Handoff Workflow

Use para transferir trabalho entre Codex, Claude Code, ChatGPT ou humano.

## Sequencia
1. Use `context-compressor` se a conversa for longa.
2. Use `handoff-builder` para estruturar contexto, arquivos, comandos e riscos.
3. Use `model-routing` para escolher proximo agente ou modelo.
4. Inclua prompt de retomada com skill sugerida.
5. Declare validacoes feitas e lacunas.

## Saidas
- Destinatario recomendado.
- Contexto minimo.
- Estado atual.
- Proximo passo.
- Prompt de retomada.
