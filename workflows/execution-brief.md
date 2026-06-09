# Execution Brief Workflow

## Objetivo
Converter pedido amplo em plano delegavel e prompts de execucao sem perder contexto, escopo ou gates de qualidade.

## Ordem recomendada
1. `agent-framework-router`: detectar intencao e escolher este workflow quando houver brief, documentacao, plano de execucao, organizacao de tarefa ou prompts por etapa.
2. `brainstorm-lab`: usar somente se objetivo, caminho ou tradeoffs ainda estiverem abertos.
3. `execution-plan-builder`: criar brief e plano enxuto.
4. `plan-quality-checker`: auditar planos de risco medio/alto, multi-arquivo, backend, API, dados, seguranca ou refatoracao grande.
5. `execution-prompt-builder`: gerar prompts por etapa quando a execucao sera delegada.
6. `handoff-builder`: usar ao trocar agente/sessao ou quando houver contexto parcial importante.
7. `code-review-gate`: depois da implementacao, decidir review adequado.

## Gates
- Nao gerar prompts finais se o plano ainda tiver tarefas vagas, aceite subjetivo ou dependencias ocultas.
- Nao mandar executar etapa de risco alto sem verificacao ou rollback proporcional.
- Nao considerar a execucao completa sem relatorio final do agente executor.
- Depois do relatorio final, encaminhar para code review antes de novas mudancas.

## Saida esperada
- Brief curto.
- Plano por etapas.
- Prompts por etapa, se solicitados.
- Instrucoes de relatorio final e code review.
